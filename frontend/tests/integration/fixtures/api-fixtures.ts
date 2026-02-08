export const testBucketData = {
  name: 'Test Business Expenses',
  description: 'A test bucket for business expense receipts'
}

export const testReceiptData = [
  { total: 25.50, vendor: 'Office Depot', notes: 'Pens and paper supplies' },
  { total: 150.00, vendor: 'Restaurant ABC', notes: 'Business lunch with client' },
  { total: 85.25, vendor: 'Shell Gas Station', notes: 'Gas for business travel' },
  { total: 42.75, vendor: 'Downtown Parking', notes: 'Parking fees for meeting' }
]

export const expectedBucketStructure = {
  required_fields: ['guid', 'name'],
  optional_fields: ['created_at', 'updated_at']
}

export const expectedReceiptStructure = {
  required_fields: ['guid', 'total', 'vendor', 'date'],
  optional_fields: ['bucket_guid', 'notes', 'allocations']
}