def apply_coupon(order_total, coupon):
    """Known bugfix context:
    Previously, expired coupons were accepted when the order total was exactly
    equal to the minimum spend threshold.
    """
    if coupon["expired"]:
        return order_total
    if order_total < coupon["min_spend"]:
        return order_total
    return order_total - coupon["discount"]


BUGFIX_NOTE = """
REQ-COUPON-001: Expired coupons must never reduce the order total.
REQ-COUPON-002: A coupon is eligible when order_total >= min_spend and it is not expired.
Generate regression tests for the fixed behavior and adjacent boundary paths.
"""
