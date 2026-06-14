import { MongoClient, type Db } from 'mongodb'
import dns from 'dns'

// Node.js sometimes uses 127.0.0.1 as DNS which can't resolve SRV records.
// Force public DNS resolvers so Atlas SRV lookup always works.
dns.setServers(['8.8.8.8', '8.8.4.4', '1.1.1.1'])

const uri = process.env.MONGODB_URI

if (!uri) {
  throw new Error(
    'MONGODB_URI is not set. Add it to landing page/.env.local\n' +
    'Get it from: cloud.mongodb.com → Connect → Drivers'
  )
}

// Parse the database name from the URI, fallback to 'officenator'
function getDbName(connectionString: string): string {
  try {
    // URI format: mongodb+srv://user:pass@host/dbname?params
    const withoutProtocol = connectionString.split('@')[1] ?? ''
    const pathPart = withoutProtocol.split('/')[1] ?? ''
    const dbName = pathPart.split('?')[0]
    return dbName || 'officenator'
  } catch {
    return 'officenator'
  }
}

const DB_NAME = getDbName(uri)

declare global {
  // eslint-disable-next-line no-var
  var _mongoClientPromise: Promise<MongoClient> | undefined
}

let clientPromise: Promise<MongoClient>

if (process.env.NODE_ENV === 'development') {
  // In dev: reuse connection across hot-reloads to avoid too-many-connections
  if (!global._mongoClientPromise) {
    const client = new MongoClient(uri)
    global._mongoClientPromise = client.connect()
    global._mongoClientPromise.catch(err => {
      console.error('[MongoDB] Connection failed:', err.message)
      global._mongoClientPromise = undefined
    })
  }
  clientPromise = global._mongoClientPromise
} else {
  const client = new MongoClient(uri)
  clientPromise = client.connect()
}

export default clientPromise

export async function getDb(): Promise<Db> {
  const client = await clientPromise
  return client.db(DB_NAME)
}
