# 订单生命周期

## 状态

- Draft：订单草稿。
- PendingPayment：待支付。
- Paid：已支付。
- Shipped：已发货。
- Completed：已完成。
- Cancelled：已取消。
- Refunded：已退款。

## 转换规则

- Draft -> PendingPayment：用户提交订单且库存锁定成功。
- PendingPayment -> Paid：支付成功。
- PendingPayment -> Cancelled：用户取消或 30 分钟超时。
- Paid -> Shipped：仓库发货。
- Shipped -> Completed：用户确认收货或 7 天自动确认。
- Paid -> Refunded：客服审核退款通过。
- Completed 不允许取消。
- Cancelled 不允许支付。

## 期望测试输出

生成 MBT 导向测试设计，包含状态转换表、非法路径、覆盖准则和最小路径集。
