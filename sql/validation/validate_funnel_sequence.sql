-- validate_funnel_sequence.sql
-- Validate that sequential funnel flags are logically consistent.
-- No session should reach checkout without reaching add_to_cart first.

-- Should return 0 rows if the funnel logic is correct.
select
    session_key,
    reached_view_item,
    reached_add_to_cart_after_view,
    reached_begin_checkout_after_cart,
    reached_purchase_after_checkout
from `YOUR_PROJECT.YOUR_DATASET.int_session_funnel`
where
    -- Checkout without cart
    (reached_begin_checkout_after_cart and not reached_add_to_cart_after_view)
    -- Purchase without checkout
    or (reached_purchase_after_checkout and not reached_begin_checkout_after_cart)
    -- Cart without view
    or (reached_add_to_cart_after_view and not reached_view_item)
limit 10;
