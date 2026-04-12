### podman

 # IPP projekt Containerfile
 # Autor : Kristian Rucek (xrucekk00)
 # VUT FIT 2026
 
# ============================================================================
# Stage 1: CHECK - For Python + TypeScript
# ============================================================================
FROM python:3.14-slim AS check

WORKDIR /workspace

# Install Node.js runtime and build dependencies for lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get remove -y curl gnupg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Python tools: ruff, mypy
RUN pip install --no-cache-dir \
    ruff==0.14.4 \
    mypy==1.19.1

# Install project dependencies needed for type checking
RUN pip install --no-cache-dir \
    pydantic~=2.12.5 \
    pydantic-xml[lxml]~=2.19.0 \
    lark==1.2.2 \
    lxml~=5.3.2 \
    types-lxml>=2026.2.16

# Install TypeScript tools: eslint, prettier
RUN npm install -g \
    eslint@9.32.0 \
    @typescript-eslint/eslint-plugin@8.52.0 \
    @typescript-eslint/parser@8.52.0 \
    prettier@3.7.* \
    typescript@5.*

# Entry point: bash shell for interactive checking
ENTRYPOINT ["/bin/bash"]

# ============================================================================
# Stage 2: BUILD - Compile Python + TypeScript
# ============================================================================
FROM check AS build

WORKDIR /IPP_Projekt

# Copy interpreter and dependencies
COPY int /IPP_Projekt/int
COPY tester /IPP_Projekt/tester

# Compile TypeScript
RUN cd /IPP_Projekt/tester && npm ci && tsc --project tsconfig.json

# ============================================================================
# build-test - Compile TypeScript tester
# ============================================================================
FROM build AS build-test

# ============================================================================
# Stage 3: RUNTIME - Minimal interpreter runtime (no dev tools)
# ============================================================================
FROM python:3.14-slim AS runtime

WORKDIR /IPP_Projekt

# Install only runtime dependencies (minimal system libs needed by Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    libxslt1.1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy pre-built Python packages from build stage (avoids recompiling lxml)
COPY --from=build /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages

# Copy compiled interpreter from build stage
COPY --from=build /IPP_Projekt/int /IPP_Projekt/int

# Set working directory
WORKDIR /IPP_Projekt/int

# Entry point: run interpreter with arguments passed through
ENTRYPOINT ["python", "src/solint.py"]

# ============================================================================
# Stage 4: TEST - Integration testing
# ============================================================================
FROM runtime AS test

WORKDIR /IPP_Projekt

# Install Node.js runtime for executing tester
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy compiled tester and dependencies from build stage
COPY --from=build /IPP_Projekt/tester/dist /IPP_Projekt/tester/dist
COPY --from=build /IPP_Projekt/tester/node_modules /IPP_Projekt/tester/node_modules
COPY --from=build /IPP_Projekt/tester/package.json /IPP_Projekt/tester/package.json
COPY --from=build /IPP_Projekt/tester/src /IPP_Projekt/tester/src

# Set working directory for tester
WORKDIR /IPP_Projekt/tester

# Entry point: run tester with arguments passed through
ENTRYPOINT ["node", "dist/tester.js"]
