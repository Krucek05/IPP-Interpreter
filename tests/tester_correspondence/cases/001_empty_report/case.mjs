#!/usr/bin/env node

import { TestReport } from "../../../../typescript/tester/dist/models.js";

const report = new TestReport({ discovered_test_cases: [], unexecuted: {}, results: {} });
console.log(JSON.stringify(report, null, 2));
