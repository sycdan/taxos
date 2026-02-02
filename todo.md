# Today's Task

Frontend Migration: Protobuf-ts to Protobuf-es
This document outlines the scope of work required to migrate the taxos frontend from @protobuf-ts to the modern @protobuf-es and Connect ecosystem. This migration will enable support for Protobuf Edition 2023 and provide a more standard-compliant gRPC-web integration.

Scope of Work
Phase 1: Dependency Overhaul
Remove Legacy Libraries: Uninstall @protobuf-ts/plugin, @protobuf-ts/runtime, @protobuf-ts/runtime-rpc, and @protobuf-ts/grpcweb-transport.
Install Modern Runtime: Install @bufbuild/protobuf (the foundational ES runtime).
Install Connect Stack: Install @connectrpc/connect and @connectrpc/connect-web for transport and client logic.
Install Build Tools: Install @bufbuild/protoc-gen-es and @connectrpc/protoc-gen-connect-es as dev dependencies.
Phase 2: Generation Workflow Update
Initialize Buf: Create a buf.yaml in the api/protos directory to manage dependencies and linting.
Configure Generation: Create a buf.gen.yaml in the ui root to define the plugins and output paths for the new ES modules.
Update Scripts: Modify package.json to use npx buf generate instead of the current protoc based command.
Phase 3: API Client & Transport Refactoring
Transport Setup: Rewrite the transport initialization in src/api/client.ts using createGrpcWebTransport from @connectrpc/connect-web.
Client Interface: Shift from the class-based generator of protobuf-ts to the functional createPromiseClient pattern.
Message Instantiation: Update calls to use constructors or the create helper, as protobuf-es does not use plain interfaces for messages.
Phase 4: Component & Type Migration
Import Updates: Search and replace imports of generated code across the application (e.g., from src/api/generated/taxos_service.ts to the new dual-file output *_pb.ts and *_connect.ts).
Type Compatibility: Adjust components that rely on the old interface structure to handle the new class-based structure (specifically handling optional fields and bigint vs string representations).
Phase 5: Verification
End-to-End Test: Verify that frontend gRPC calls still reach the envoy proxy and are processed by the api service.
Persistence Test: Confirm data integrity is maintained through the full gRPC-web to gRPC transition.
Why this is necessary for Edition 2023
The current @protobuf-ts library uses a custom reflection-based generator that does not recognize the new edition keyword. protobuf-es is built specifically to support the future of Protobuf, including lexical scoping and feature-based defaults.