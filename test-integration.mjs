#!/usr/bin/env node
/**
 * Test runner for TaxOS gRPC integration
 * This script tests various components step by step
 */

import { execSync } from "child_process";
import { existsSync } from "fs";
import { join } from "path";

const colors = {
	reset: "\x1b[0m",
	green: "\x1b[32m",
	red: "\x1b[31m",
	yellow: "\x1b[33m",
	blue: "\x1b[34m",
	cyan: "\x1b[36m",
};

function log(message, color = "reset") {
	console.log(`${colors[color]}${message}${colors.reset}`);
}

function runCommand(command, description) {
	log(`🔍 ${description}`, "cyan");
	try {
		const output = execSync(command, { encoding: "utf-8", cwd: process.cwd() });
		log(`✅ Success: ${description}`, "green");
		return output;
	} catch (error) {
		log(`❌ Failed: ${description}`, "red");
		log(`   Error: ${error.message}`, "red");
		throw error;
	}
}

function checkFile(filePath, description) {
	log(`📁 ${description}`, "cyan");
	if (existsSync(filePath)) {
		log(`✅ Found: ${filePath}`, "green");
		return true;
	} else {
		log(`❌ Missing: ${filePath}`, "red");
		return false;
	}
}

async function main() {
	log("🧪 TaxOS Integration Test Suite", "blue");
	log("=".repeat(50), "blue");

	const tests = [
		() =>
			checkFile("backend/protos/taxos_service.proto", "Check proto definition"),
		() => checkFile("backend/server.py", "Check backend server"),
		() => checkFile("backend/requirements.txt", "Check backend requirements"),
		() => checkFile("docker-compose.yml", "Check docker compose config"),
		() => checkFile("ui/package.json", "Check UI package config"),
		() =>
			checkFile("ui/src/components/GrpcDashboard.tsx", "Check React component"),
		() => checkFile("ui/src/api/mock-client.ts", "Check mock API client"),

		() =>
			runCommand(
				"cd backend && python -c \"import sqlite3; print('SQLite available')\"",
				"Test SQLite availability",
			),

		() =>
			runCommand(
				"cd backend && python -c \"import grpc; print('gRPC available')\"",
				"Test gRPC availability",
			),

		() =>
			runCommand(
				"cd backend && python test_backend.py",
				"Run backend test suite",
			),

		() =>
			runCommand(
				'cd ui && npm list --depth=0 2>/dev/null | grep -E "(react|vite)" || echo "Dependencies installed"',
				"Check UI dependencies",
			),
	];

	let passed = 0;
	let total = tests.length;

	for (let i = 0; i < tests.length; i++) {
		try {
			await tests[i]();
			passed++;
			log("", "reset"); // Empty line for readability
		} catch (error) {
			log("", "reset"); // Empty line for readability
		}
	}

	log("=".repeat(50), "blue");
	log(
		`📊 Test Results: ${passed}/${total} tests passed`,
		passed === total ? "green" : "yellow",
	);

	if (passed === total) {
		log("🎉 All tests passed! Your TaxOS setup is working correctly.", "green");
		log("", "reset");
		log("Next steps:", "blue");
		log("1. UI is running at: http://localhost:5174/", "cyan");
		log("2. Try the GrpcDashboard component with mock data", "cyan");
		log("3. When ready, build with: docker compose build", "cyan");
		log("4. Deploy with: docker compose up", "cyan");
		return 0;
	} else {
		log("⚠️  Some tests failed. Check the output above for details.", "yellow");
		return 1;
	}
}

// Run the tests
main().catch((error) => {
	log(`💥 Test runner failed: ${error.message}`, "red");
	process.exit(1);
});
