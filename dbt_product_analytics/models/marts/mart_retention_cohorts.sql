{{
  config(
    materialized='table'
  )
}}

/*
  Mart: mart_retention_cohorts
  Grain: One row per (cohort_week, activity_week_index)
  
  Weekly activity retention cohorts.
  
  - cohort_week: The ISO week of a user's FIRST observed session
  - activity_week_index: 0 = cohort week, 1 = the next week, etc.
  - A user is "retained" if they had ANY session in that week
  
  IMPORTANT: This is observed activity retention within the data window.
  It is NOT a full long-term retention estimate. Users may return outside
  the data window and not be counted. See docs/limitations.md.
*/

with user_first_week as (
    select
        user_pseudo_id,
        date_trunc(min(session_date), week(monday)) as cohort_week
    from {{ ref('int_sessions') }}
    group by user_pseudo_id
),

user_activity_weeks as (
    select distinct
        s.user_pseudo_id,
        date_trunc(s.session_date, week(monday)) as activity_week
    from {{ ref('int_sessions') }} s
),

cohort_activity as (
    select
        ufw.cohort_week,
        uaw.activity_week,
        date_diff(uaw.activity_week, ufw.cohort_week, week) as activity_week_index,
        count(distinct uaw.user_pseudo_id) as retained_users
    from user_first_week ufw
    inner join user_activity_weeks uaw
        on ufw.user_pseudo_id = uaw.user_pseudo_id
    group by ufw.cohort_week, uaw.activity_week
),

cohort_sizes as (
    select
        cohort_week,
        count(distinct user_pseudo_id) as cohort_size
    from user_first_week
    group by cohort_week
)

select
    ca.cohort_week,
    ca.activity_week,
    ca.activity_week_index,
    cs.cohort_size,
    ca.retained_users,
    safe_divide(ca.retained_users, cs.cohort_size) as retention_rate

from cohort_activity ca
inner join cohort_sizes cs
    on ca.cohort_week = cs.cohort_week

where ca.activity_week_index >= 0

order by ca.cohort_week, ca.activity_week_index
