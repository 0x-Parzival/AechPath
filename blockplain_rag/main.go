// Initialize API server
server := api.NewBlockServer(p, pool)

// Set up hooks to broadcast new blocks and transactions
// This could be done by modifying the AddBlock method in plane.go
// and AddTransaction in txpool.go

// Start the API server in a goroutine
go server.Start(8080)