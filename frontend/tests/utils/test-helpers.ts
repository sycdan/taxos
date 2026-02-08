export const waitForCondition = async (
    conditionFn: () => Promise<boolean>,
    timeout: number = 10000,
    interval: number = 1000
): Promise<void> => {
    const startTime = Date.now()

    while (Date.now() - startTime < timeout) {
        if (await conditionFn()) {
            return
        }
        await new Promise(resolve => setTimeout(resolve, interval))
    }

    throw new Error(`Condition not met within ${timeout}ms`)
}

export const generateTestData = (overrides: any = {}) => {
    return {
        name: `Test-${Date.now()}`,
        description: 'Generated test data',
        ...overrides
    }
}

export const assertApiResponse = (response: any, expectedFields: string[]) => {
    expectedFields.forEach(field => {
        if (response[field] === undefined) {
            throw new Error(`Expected field '${field}' not found in response`)
        }
    })
}

export const cleanupTestData = async (apiClient: any, resourceId: string, resourceType: string) => {
    try {
        switch (resourceType) {
            case 'taxonomy':
                await apiClient.deleteTaxonomy(resourceId)
                break
            // Add more cleanup types as needed
        }
        console.log(`✅ Cleaned up ${resourceType}: ${resourceId}`)
    } catch (error) {
        console.warn(`⚠️ Failed to cleanup ${resourceType} ${resourceId}:`, error)
    }
}