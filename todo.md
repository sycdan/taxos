# To Do: Taxos Development

We need to figure out how to upload receipt files via the UI.

I am thinking we can have ./data/uploads where we will store zips named for the hash of the uploaded file (provided by the frontend, and verified by the backend).

The flow will be:

- User drags a file over the website and drops it
- We hash the file on the client side
- We upload it (endpoint does not exist yet) and save it in compressed format (we can preserve the filename inside the zip)
- After uploading, we show the user the add receipt modal
- When they submit, the post includes the file hash, so the receipt becomes implicitly linked to the upload via the hash (we can add download capability in future if necessary this way)

---

## Today's Tasks

### 🔧 Backend Implementation
- [ ] **Create upload directory structure**: Set up `./backend/data/uploads/` directory
- [ ] **Add upload endpoint to proto**: Define `UploadReceiptFile` RPC in `taxos_service.proto`
- [ ] **Implement file upload handler**: Create backend logic to:
  - Check if file hash already exists (idempotency)
  - Return existing file info if hash found (avoid re-upload)
  - Receive multipart file uploads for new files
  - Validate file hash matches client-provided hash  
  - Compress and save files as named zips
  - Return upload confirmation with hash
- [ ] **Generate proto bindings**: Run protobuf generation for new endpoints

### 🎨 Frontend Implementation  
- [?] **Create file upload component**: Build drag-and-drop file upload interface (should be mostly done, but check)
- [ ] **Implement client-side hashing**: Add SHA-256 hashing for uploaded files
- [ ] **Integrate with receipt modal**: Update `ReceiptModal.tsx` to show upload progress where the cancel button currently is (we can remove cancel button) -- open it immediately when dropping the filem, to allow used to enter info while uploading
- [ ] **File validation**: Ensure only image/PDF files are accepted

### 🔗 API Integration
- [ ] **Update API client**: Add upload/download methods to frontend API client
- [ ] **Error handling**: Implement proper error states for upload failures  
- [ ] **Update receipt creation**: Modify receipt creation to include file hash

### ✅ Testing & Polish
- [ ] **Test upload flow**: End-to-end testing of file upload → receipt creation
- [ ] **UI polish**: Improve visual feedback and user experience

---

## Priority Order
1. Backend proto definition and file handling
2. Frontend upload component and hashing
3. API integration and testing
4. Polish

## Notes
- File storage in `/backend/data/uploads/{hash}.zip` format
- Client-side hashing prevents upload conflicts
- Receipt `hash` field already exist in proto schema
- **IMPORTANT**: Upload endpoint must be idempotent - check if hash exists before accepting upload
- Duplicate file uploads should return success without re-processing


