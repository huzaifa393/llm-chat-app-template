#!/bin/bash
echo "========================================="
echo "  Islamic RAG - System Status Report"
echo "========================================="
echo "Date: $(date)"
echo ""

echo "📦 PACKAGES:"
for pkg in chromadb boto3 PyPDF2 pdfminer streamlit; do
    pip3.11 show $pkg 2>/dev/null | grep -q "Name" && echo "✅ $pkg" || echo "❌ $pkg"
done

echo -e "\n💾 STORAGE:"
df -h ~ | grep -v "Filesystem"

echo -e "\n📊 CHROMADB:"
python3.11 -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
try:
    coll = client.get_collection('islamic_texts')
    print(f'   ✅ Collection: islamic_texts ({coll.count():,} docs)')
except:
    print('   ❌ Collection not found')
"

echo -e "\n📁 LOCAL FILES:"
for dir in pdf_books csv_books processed_books; do
    if [ -d "$dir" ]; then
        count=$(find "$dir" -type f 2>/dev/null | wc -l)
        echo "   📂 $dir: $count files"
    fi
done

echo -e "\n☁️  S3 STATUS:"
BUCKET="islamic-rag-books"
aws s3 ls s3://$BUCKET 2>/dev/null | grep -q "PRE" && echo "   ✅ Bucket accessible" || echo "   ❌ Bucket not accessible"

echo -e "\n🚀 APP STATUS:"
curl -s http://localhost:8501 > /dev/null && echo "   ✅ Streamlit running" || echo "   ❌ Streamlit not running"

echo -e "\n========================================="
