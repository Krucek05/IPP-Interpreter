### podman

# ============================================================================
# Stage 1: check - Quality code checking (mypy, ruff)
# ============================================================================
FROM python:3.14-slim AS check

WORKDIR /workspace

# Install ruff and mypy and project dependencies
RUN pip install --no-cache-dir ruff==0.14.* mypy==1.19.* pydantic==2.12.* pydantic-xml==2.19.* lxml==6.0.*

# Entry point: bash shell for interactive checking
ENTRYPOINT ["/bin/bash"]

# ============================================================================
# Stage 2: build - Compile/prepare Python interpreter
# ============================================================================
FROM python:3.14-slim AS build

WORKDIR /IPP_Projekt

# Copy interpreter source and dependencies
COPY python/int /IPP_Projekt/int

# Install interpreter dependencies
RUN cd /IPP_Projekt/int && pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 3: build-test - Compile TypeScript tester
# ============================================================================
FROM node:24.12-slim AS build-test

WORKDIR /IPP_Projekt

# Copy tester source
COPY typescript/tester /IPP_Projekt/tester

# Install tester dependencies and build
RUN cd /IPP_Projekt/tester && npm ci && npm run build

# ============================================================================
# Stage 4: runtime - Minimal Python interpreter image
# ============================================================================
FROM python:3.14-slim AS runtime

WORKDIR /IPP_Projekt

# Copy installed packages and source from build stage
COPY --from=build /IPP_Projekt/int /IPP_Projekt/int
COPY --from=build /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages

# Entry point: run interpreter with XML input
ENTRYPOINT ["python", "/IPP_Projekt/int/src/solint.py"]

# ============================================================================
# Stage 5: test - Integration testing
# ============================================================================
FROM runtime AS test

WORKDIR /IPP_Projekt

# Install Node.js for running the tester
RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm && rm -rf /var/lib/apt/lists/*

# Copy compiled tester from build-test stage
COPY --from=build-test /IPP_Projekt/tester /IPP_Projekt/tester

# Entry point: run tester
ENTRYPOINT ["node", "/IPP_Projekt/tester/dist/tester.js"]

