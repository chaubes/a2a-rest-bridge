import type { OrderConfirmation, OrderStatus } from '../types'

interface Props {
  order: OrderConfirmation
}

function statusConfig(status: OrderStatus): {
  label: string
  classes: string
} {
  const lower = status.toLowerCase()
  if (lower === 'confirmed' || lower === 'completed') {
    return {
      label: 'Confirmed',
      classes: 'bg-green-100 text-green-800 ring-green-200',
    }
  }
  if (lower === 'failed' || lower === 'error') {
    return {
      label: 'Failed',
      classes: 'bg-red-100 text-red-800 ring-red-200',
    }
  }
  if (lower === 'pending_review' || lower === 'pending') {
    return {
      label: 'Pending Review',
      classes: 'bg-amber-100 text-amber-800 ring-amber-200',
    }
  }
  return {
    label: status,
    classes: 'bg-gray-100 text-gray-700 ring-gray-200',
  }
}

function formatCurrency(
  amount: number | undefined,
  currency: string | undefined,
): string {
  if (amount === undefined) return '—'
  const code = currency ?? 'USD'
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: code,
    }).format(amount)
  } catch {
    return `${code} ${amount.toFixed(2)}`
  }
}

interface RowProps {
  label: string
  value: React.ReactNode
}

function Row({ label, value }: RowProps) {
  return (
    <div className="flex justify-between items-baseline gap-4 py-1.5 border-b border-gray-100 last:border-0">
      <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide whitespace-nowrap">
        {label}
      </dt>
      <dd className="text-sm text-gray-900 text-right break-all">{value}</dd>
    </div>
  )
}

export default function OrderConfirmationCard({ order }: Props) {
  const { label, classes } = statusConfig(order.status)
  const isFailed =
    order.status.toLowerCase() === 'failed' ||
    order.status.toLowerCase() === 'error'

  return (
    <div
      role="region"
      aria-label="Order confirmation"
      className="mt-3 rounded-2xl border border-gray-200 bg-gray-50 shadow-sm overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200">
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Order
          </p>
          <p className="text-sm font-semibold text-gray-900 font-mono">
            {order.order_id || '—'}
          </p>
        </div>
        <span
          className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ring-1 ring-inset ${classes}`}
        >
          {label}
        </span>
      </div>

      {/* Failure reason — shown prominently at top when present */}
      {isFailed && order.failure_reason && (
        <div className="px-4 py-3 bg-red-50 border-b border-red-100 flex gap-2 items-start">
          <svg
            className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2}
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
            />
          </svg>
          <p className="text-sm text-red-700">{order.failure_reason}</p>
        </div>
      )}

      {/* Details */}
      <dl className="px-4 py-3 space-y-0">
        {order.customer_name && (
          <Row label="Customer" value={order.customer_name} />
        )}
        {order.product_name && (
          <Row label="Product" value={order.product_name} />
        )}
        {order.quantity !== undefined && (
          <Row label="Quantity" value={order.quantity} />
        )}
        {order.unit_price !== undefined && (
          <Row
            label="Unit price"
            value={formatCurrency(order.unit_price, order.currency)}
          />
        )}
        {order.total_amount !== undefined && (
          <Row
            label="Total"
            value={
              <span className="font-semibold">
                {formatCurrency(order.total_amount, order.currency)}
              </span>
            }
          />
        )}
        {order.transaction_id && (
          <Row
            label="Transaction"
            value={
              <span className="font-mono text-xs">{order.transaction_id}</span>
            }
          />
        )}
        {order.tracking_id && (
          <Row
            label="Tracking"
            value={
              <span className="font-mono text-xs">{order.tracking_id}</span>
            }
          />
        )}
        {order.estimated_delivery && (
          <Row label="Est. delivery" value={order.estimated_delivery} />
        )}
        {!isFailed && order.failure_reason && (
          <Row label="Note" value={order.failure_reason} />
        )}
      </dl>

      {/* Correlation ID footer */}
      {order.correlation_id && (
        <div className="px-4 py-2 bg-gray-100 border-t border-gray-200">
          <p className="text-xs text-gray-400">
            <span className="font-medium text-gray-500">Correlation ID: </span>
            <span className="font-mono">{order.correlation_id}</span>
          </p>
        </div>
      )}
    </div>
  )
}
