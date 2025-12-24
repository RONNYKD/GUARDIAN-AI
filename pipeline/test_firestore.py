"""
Test Firestore Native Mode Database Connection
"""
import os
from google.cloud import firestore
from datetime import datetime

# Set environment
os.environ['GCP_PROJECT_ID'] = 'lovable-clone-e08db'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'd:\SENTINEL (for the google accelerator hackerthon)\lovable-clone-e08db-56b9ffba4711.json'
os.environ['FIRESTORE_DATABASE'] = 'guardianai'

print("=" * 70)
print("Firestore Native Mode Test")
print("=" * 70)

try:
    # Initialize Firestore client with named database
    print("\n📡 Connecting to Firestore...")
    db = firestore.Client(
        project='lovable-clone-e08db',
        database='guardianai'
    )
    print("✅ Connected to database: guardianai")
    
    # Test: Create a document
    print("\n📝 Creating test document...")
    doc_ref = db.collection('test').document('test_doc')
    doc_ref.set({
        'message': 'Hello from GuardianAI!',
        'timestamp': datetime.now(),
        'status': 'testing',
        'database_mode': 'FIRESTORE_NATIVE'
    })
    print("✅ Document created successfully")
    
    # Test: Read the document
    print("\n📖 Reading test document...")
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        print("✅ Document retrieved:")
        print(f"   Message: {data['message']}")
        print(f"   Status: {data['status']}")
        print(f"   Database Mode: {data['database_mode']}")
    else:
        print("❌ Document not found")
    
    # Test: Update the document
    print("\n✏️  Updating test document...")
    doc_ref.update({
        'status': 'verified',
        'updated_at': datetime.now()
    })
    print("✅ Document updated successfully")
    
    # Test: Query documents
    print("\n🔍 Querying test collection...")
    docs = db.collection('test').where('status', '==', 'verified').get()
    print(f"✅ Found {len(docs)} document(s)")
    
    # Test: Delete the document
    print("\n🗑️  Cleaning up test document...")
    doc_ref.delete()
    print("✅ Document deleted successfully")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED - Firestore Native Mode Working!")
    print("=" * 70)
    print("\n🎉 Database 'guardianai' is ready for use!")
    print("\nNext steps:")
    print("  1. Update pipeline/main.py to use the new database")
    print("  2. Update backend services to use database='guardianai'")
    print("  3. Test full pipeline with Firestore storage")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    print("\n⚠️  Troubleshooting:")
    print("  1. Verify database was created: gcloud firestore databases list")
    print("  2. Check credentials are correct")
    print("  3. Ensure service account has Firestore permissions")
