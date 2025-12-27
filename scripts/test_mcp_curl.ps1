# Test MCP Server with curl
# This demonstrates the MCP protocol format

$serverUrl = "http://localhost:8000"

Write-Host "=" * 60
Write-Host "Testing MCP Server with curl"
Write-Host "=" * 60
Write-Host ""

# Test 1: List available tools
Write-Host "Test 1: List available tools" -ForegroundColor Cyan
Write-Host "Request: tools/list" -ForegroundColor Gray
Write-Host ""

$listToolsRequest = @{
    jsonrpc = "2.0"
    id = 1
    method = "tools/list"
    params = @{}
} | ConvertTo-Json -Depth 10

$response = curl.exe -s -X POST `
    -H "Content-Type: application/json" `
    -d $listToolsRequest `
    $serverUrl

Write-Host "Response:" -ForegroundColor Green
$response | ConvertFrom-Json | ConvertTo-Json -Depth 10
Write-Host ""
Write-Host ""

# Test 2: Call get_user_schema tool
Write-Host "Test 2: Call get_user_schema" -ForegroundColor Cyan
Write-Host "Request: tools/call -> get_user_schema" -ForegroundColor Gray
Write-Host ""

$getUserSchemaRequest = @{
    jsonrpc = "2.0"
    id = 2
    method = "tools/call"
    params = @{
        name = "get_user_schema"
        arguments = @{}
    }
} | ConvertTo-Json -Depth 10

$response = curl.exe -s -X POST `
    -H "Content-Type: application/json" `
    -d $getUserSchemaRequest `
    $serverUrl

Write-Host "Response:" -ForegroundColor Green
$response | ConvertFrom-Json | ConvertTo-Json -Depth 10
Write-Host ""
Write-Host ""

# Test 3: Call create_entity_type
Write-Host "Test 3: Call create_entity_type" -ForegroundColor Cyan
Write-Host "Request: tools/call -> create_entity_type" -ForegroundColor Gray
Write-Host ""

$createEntityTypeRequest = @{
    jsonrpc = "2.0"
    id = 3
    method = "tools/call"
    params = @{
        name = "create_entity_type"
        arguments = @{
            entity_type_name = "note"
            schema_definition = @{
                title = @{
                    type = "string"
                    required = $true
                }
                content = @{
                    type = "string"
                }
                tags = @{
                    type = "array"
                }
            }
        }
    }
} | ConvertTo-Json -Depth 10

$response = curl.exe -s -X POST `
    -H "Content-Type: application/json" `
    -d $createEntityTypeRequest `
    $serverUrl

Write-Host "Response:" -ForegroundColor Green
$response | ConvertFrom-Json | ConvertTo-Json -Depth 10
Write-Host ""
Write-Host ""

# Test 4: Call create_entity
Write-Host "Test 4: Call create_entity" -ForegroundColor Cyan
Write-Host "Request: tools/call -> create_entity" -ForegroundColor Gray
Write-Host ""

$createEntityRequest = @{
    jsonrpc = "2.0"
    id = 4
    method = "tools/call"
    params = @{
        name = "create_entity"
        arguments = @{
            entity_type = "note"
            data = @{
                title = "My first note"
                content = "Testing the MCP server with curl!"
                tags = @("test", "curl", "mcp")
            }
            metadata = @{
                createdBy = "curl-test"
                source = "manual-test"
            }
        }
    }
} | ConvertTo-Json -Depth 10

$response = curl.exe -s -X POST `
    -H "Content-Type: application/json" `
    -d $createEntityRequest `
    $serverUrl

Write-Host "Response:" -ForegroundColor Green
$response | ConvertFrom-Json | ConvertTo-Json -Depth 10
Write-Host ""
Write-Host ""

# Test 5: List entities
Write-Host "Test 5: Call list_entities" -ForegroundColor Cyan
Write-Host "Request: tools/call -> list_entities" -ForegroundColor Gray
Write-Host ""

$listEntitiesRequest = @{
    jsonrpc = "2.0"
    id = 5
    method = "tools/call"
    params = @{
        name = "list_entities"
        arguments = @{
            entity_type = "note"
            limit = 10
        }
    }
} | ConvertTo-Json -Depth 10

$response = curl.exe -s -X POST `
    -H "Content-Type: application/json" `
    -d $listEntitiesRequest `
    $serverUrl

Write-Host "Response:" -ForegroundColor Green
$response | ConvertFrom-Json | ConvertTo-Json -Depth 10
Write-Host ""

Write-Host "=" * 60
Write-Host "Tests complete!" -ForegroundColor Green
Write-Host "=" * 60
