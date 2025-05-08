package api

import (
	"blockplain/block"
	"blockplain/plane"
	"blockplain/txpool"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/mux"
	"github.com/gorilla/websocket"
)

// BlockServer manages the HTTP API for the blockchain
type BlockServer struct {
	plane   *plane.Plane
	txPool  *txpool.TxPool
	clients map[*websocket.Conn]bool
	mutex   sync.Mutex
}

// NewBlockServer creates a new API server
func NewBlockServer(p *plane.Plane, tp *txpool.TxPool) *BlockServer {
	return &BlockServer{
		plane:   p,
		txPool:  tp,
		clients: make(map[*websocket.Conn]bool),
	}
}

// Start launches the HTTP server
func (s *BlockServer) Start(port int) {
	r := mux.NewRouter()

	// REST API routes
	r.HandleFunc("/blocks", s.getBlocks).Methods("GET")
	r.HandleFunc("/blocks/{x}/{y}", s.getBlock).Methods("GET")
	r.HandleFunc("/transactions", s.getTransactions).Methods("GET")
	r.HandleFunc("/state", s.getState).Methods("GET")

	// WebSocket endpoint for real-time updates
	r.HandleFunc("/ws", s.handleWebSocket)

	// Start the server
	addr := fmt.Sprintf(":%d", port)
	fmt.Printf("BlockPlain API server starting on %s\n", addr)
	log.Fatal(http.ListenAndServe(addr, r))
}

// getBlocks returns all blocks in the blockchain
func (s *BlockServer) getBlocks(w http.ResponseWriter, r *http.Request) {
	blocks := []block.Block{}
	for x := range s.plane.Grid {
		for y := range s.plane.Grid[x] {
			if s.plane.Grid[x][y] != nil {
				blocks = append(blocks, *s.plane.Grid[x][y])
			}
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(blocks)
}

// getBlock returns a specific block by coordinates
func (s *BlockServer) getBlock(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	x, y := 0, 0
	fmt.Sscanf(vars["x"], "%d", &x)
	fmt.Sscanf(vars["y"], "%d", &y)

	block := s.plane.GetBlock(x, y)
	if block == nil {
		http.Error(w, "Block not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(block)
}

// getTransactions returns all transactions in the pool
func (s *BlockServer) getTransactions(w http.ResponseWriter, r *http.Request) {
	txs := s.txPool.GetTransactionsWithoutFlushing()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(txs)
}

// getState returns a summary of the blockchain state
func (s *BlockServer) getState(w http.ResponseWriter, r *http.Request) {
	blockCount := 0
	txCount := 0
	latestX, latestY := 0, 0
	latestTimestamp := time.Time{}

	// Count blocks and find the latest one
	for x := range s.plane.Grid {
		for y := range s.plane.Grid[x] {
			if s.plane.Grid[x][y] != nil {
				blockCount++
				for _, tx := range s.plane.Grid[x][y].Data {
					if tx != "Genesis" {
						txCount++
					}
				}

				// Check if this is the latest block
				if s.plane.Grid[x][y].Timestamp.After(latestTimestamp) {
					latestTimestamp = s.plane.Grid[x][y].Timestamp
					latestX, latestY = x, y
				}
			}
		}
	}

	// Add pending transactions
	pendingTxs := s.txPool.GetTransactionsWithoutFlushing()
	pendingTxCount := len(pendingTxs)

	state := map[string]interface{}{
		"blockCount":      blockCount,
		"txCount":         txCount,
		"pendingTxCount":  pendingTxCount,
		"latestBlock":     map[string]int{"x": latestX, "y": latestY},
		"latestTimestamp": latestTimestamp,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(state)
}

// WebSocket upgrade configuration
var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin: func(r *http.Request) bool {
		return true // Allow all connections for demo
	},
}

// handleWebSocket manages WebSocket connections for real-time updates
func (s *BlockServer) handleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WebSocket upgrade error: %v", err)
		return
	}
	defer conn.Close()

	// Register client
	s.mutex.Lock()
	s.clients[conn] = true
	s.mutex.Unlock()

	// Handle disconnect
	defer func() {
		s.mutex.Lock()
		delete(s.clients, conn)
		s.mutex.Unlock()
	}()

	// Keep connection alive
	for {
		_, _, err := conn.ReadMessage()
		if err != nil {
			break
		}
	}
}

// BroadcastNewBlock sends a new block to all connected WebSocket clients
func (s *BlockServer) BroadcastNewBlock(b *block.Block) {
	message := map[string]interface{}{
		"type":      "newBlock",
		"timestamp": time.Now(),
		"data":      b,
	}

	jsonMessage, err := json.Marshal(message)
	if err != nil {
		log.Printf("Error marshaling block: %v", err)
		return
	}

	s.mutex.Lock()
	for client := range s.clients {
		err := client.WriteMessage(websocket.TextMessage, jsonMessage)
		if err != nil {
			log.Printf("Error sending to client: %v", err)
			client.Close()
			delete(s.clients, client)
		}
	}
	s.mutex.Unlock()
}

// BroadcastNewTransaction sends a new transaction to all connected WebSocket clients
func (s *BlockServer) BroadcastNewTransaction(tx txpool.Transaction) {
	message := map[string]interface{}{
		"type":      "newTransaction",
		"timestamp": time.Now(),
		"data":      tx,
	}

	jsonMessage, err := json.Marshal(message)
	if err != nil {
		log.Printf("Error marshaling transaction: %v", err)
		return
	}

	s.mutex.Lock()
	for client := range s.clients {
		err := client.WriteMessage(websocket.TextMessage, jsonMessage)
		if err != nil {
			log.Printf("Error sending to client: %v", err)
			client.Close()
			delete(s.clients, client)
		}
	}
	s.mutex.Unlock()
}