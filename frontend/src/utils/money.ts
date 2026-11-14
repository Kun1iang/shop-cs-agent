const formatter = new Intl.NumberFormat('zh-CN', {
  style: 'currency',
  currency: 'CNY',
  minimumFractionDigits: 2,
})

export function formatMoney(amountCents: number): string {
  return formatter.format(amountCents / 100)
}

