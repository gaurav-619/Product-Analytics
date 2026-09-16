{{
  config(
    materialized='table'
  )
}}

/*
  Mart: mart_customer_rfm
  Grain: One row per purchaser (user_pseudo_id)
  
  RFM (Recency, Frequency, Monetary) segmentation for purchasers only.
  
  Scoring:
  - Uses NTILE(5) to create quintile-based scores
  - Recency: LOWER days since last purchase = BETTER → score 5 is most recent
  - Frequency: HIGHER order count = BETTER → score 5 is most frequent
  - Monetary: HIGHER revenue = BETTER → score 5 is highest value
  
  Reference date: The maximum order date in the dataset (not current date),
  since this is historical data.
  
  Segment labels are neutral descriptive categories based on RFM score combinations.
  They are NOT causal claims about customer behavior.
*/

with purchaser_metrics as (
    select
        user_pseudo_id,
        count(distinct order_transaction_key) as frequency,
        sum(order_revenue_usd) as monetary_value_usd,
        max(order_date) as last_order_date,
        min(order_date) as first_order_date
    from {{ ref('int_orders') }}
    group by user_pseudo_id
),

-- Use the max order date in the dataset as the reference point
reference_date as (
    select max(order_date) as ref_date
    from {{ ref('int_orders') }}
),

recency_calc as (
    select
        pm.*,
        rd.ref_date,
        date_diff(rd.ref_date, pm.last_order_date, day) as recency_days
    from purchaser_metrics pm
    cross join reference_date rd
),

-- RFM scoring with NTILE(5)
-- Lower recency_days is better, so we reverse the NTILE ordering
rfm_scores as (
    select
        *,
        -- Recency: score 5 = most recent (lowest recency_days)
        ntile(5) over (order by recency_days desc) as r_score,
        -- Frequency: score 5 = most frequent
        ntile(5) over (order by frequency asc) as f_score,
        -- Monetary: score 5 = highest value
        ntile(5) over (order by monetary_value_usd asc) as m_score
    from recency_calc
),

labeled as (
    select
        *,
        -- Composite RFM segment label
        case
            -- Champions: High across all dimensions
            when r_score >= 4 and f_score >= 4 and m_score >= 4
                then 'Champions'
            
            -- Loyal Customers: High frequency, decent recency
            when f_score >= 4 and r_score >= 3
                then 'Loyal Customers'
            
            -- Potential Loyalists: Recent with moderate frequency
            when r_score >= 4 and f_score >= 2 and f_score <= 3
                then 'Potential Loyalists'
            
            -- Recent Customers: Very recent, low frequency (new buyers)
            when r_score >= 4 and f_score = 1
                then 'Recent Customers'
            
            -- At Risk: Were good customers but haven't purchased recently
            when r_score <= 2 and f_score >= 3
                then 'At Risk'
            
            -- Everyone else
            else 'Occasional Customers'
        end as rfm_segment
    
    from rfm_scores
)

select
    user_pseudo_id,
    recency_days,
    frequency,
    monetary_value_usd,
    first_order_date,
    last_order_date,
    ref_date as analysis_reference_date,
    r_score,
    f_score,
    m_score,
    rfm_segment

from labeled
