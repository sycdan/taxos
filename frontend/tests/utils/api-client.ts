export class TaxosApiClient {
  private token: string = '77e96aa7035ffea5e9750a705ed919104274ad7ac924d10a2d7b23c1b8b7c60c'

  constructor(private baseUrl: string = 'http://backend:50051') { }

  private get headers() {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.token}`
    }
  }

  async listBuckets() {
    const response = await fetch(`${this.baseUrl}/taxos.v1.TaxosApi/ListBuckets`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({}),
    })

    if (!response.ok) {
      throw new Error(`Failed to list buckets: ${response.statusText}`)
    }

    return response.json()
  }

  async createBucket(name: string) {
    const response = await fetch(`${this.baseUrl}/taxos.v1.TaxosApi/CreateBucket`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ name }),
    })

    if (!response.ok) {
      throw new Error(`Failed to create bucket: ${response.statusText}`)
    }

    return response.json()
  }

  async getBucket(guid: string) {
    const response = await fetch(`${this.baseUrl}/taxos.v1.TaxosApi/GetBucket`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ guid }),
    })

    if (!response.ok) {
      throw new Error(`Failed to get bucket: ${response.statusText}`)
    }

    return response.json()
  }

  async updateBucket(guid: string, name: string) {
    const response = await fetch(`${this.baseUrl}/taxos.v1.TaxosApi/UpdateBucket`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ guid, name }),
    })

    if (!response.ok) {
      throw new Error(`Failed to update bucket: ${response.statusText}`)
    }

    return response.json()
  }

  async deleteBucket(guid: string) {
    const response = await fetch(`${this.baseUrl}/taxos.v1.TaxosApi/DeleteBucket`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ guid }),
    })

    if (!response.ok) {
      throw new Error(`Failed to delete bucket: ${response.statusText}`)
    }

    return response.json()
  }

async createReceipt(total: number, vendor: string, notes?: string) {
    const response = await fetch(`${this.baseUrl}/taxos.v1.TaxosApi/CreateReceipt`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ 
        total: total,
        vendor: vendor,
        date: new Date().toISOString(),
        timezone: 'UTC',
        notes: notes || '',
        allocations: []
      }),
    })

    if (!response.ok) {
      throw new Error(`Failed to create receipt: ${response.statusText}`)
    }

    return response.json()
  }

  async listUnallocatedReceipts() {
    const response = await fetch(`${this.baseUrl}/taxos.v1.TaxosApi/ListUnallocatedReceipts`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({}),
    })

    if (!response.ok) {
      throw new Error(`Failed to list unallocated receipts: ${response.statusText}`)
    }

    return response.json()
  }
}