import { useState } from 'react'
import axios from 'axios'
import './App.css'
import ReactFlow , { Background, Controls } from 'reactflow'
import 'reactflow/dist/style.css'


function App() {
  const [inputText , setInputText] = useState('');
  const [resolvedText , setResolvedText] = useState('');
  const [nodes , setNodes] = useState([]);
  const [edges , setEdges] = useState([]);

  const handleResolveClick = async () => {
    if (!inputText) return;

    try {
    
      const response = await axios.post('http://localhost:8000/api/resolve', {
        raw_text: inputText
      });
      
      setResolvedText(response.data.dummy_ai_resolution);

      const flowNodes = response.data.dummy_graph_data.nodes.map((node, index) => ({
        id: node.id,
        data: { label: node.label },
        position: { x: 250, y: index * 120 + 100 }, // Stacks them vertically
        style: {
          background: node.type === 'conflict' ? '#ef4444' : '#374151', // Red for conflict, grey for dep
          color: 'white',
          border: '1px solid #1f2937',
          borderRadius: '8px',
          padding: '12px',
          fontWeight: 'bold'
        }
      }));

      const flowEdges = response.data.dummy_graph_data.edges.map(edge => ({
        id: `${edge.source}-${edge.target}`,
        source: edge.source,
        target: edge.target,
        animated: true, // Makes the connection line flow visually!
        style: { stroke: '#60a5fa', strokeWidth: 2 }
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);

    } catch (error) {
      console.error("Error during API call:", error);
      setResolvedText("// Error: Unable to resolve conflict. Please check the input or try again later.");
    }

  }

  return (
    <div className="h-screen w-full bg-gray-900 text-white flex flex-col font-sans">
      
      {/* Top Navbar */}
      <header className="p-4 border-b border-gray-700 bg-gray-800">
        <h1 className="text-xl font-bold text-blue-400">Git Conflict Resolver & Impact Simulator</h1>
      </header>

      {/* Main Dashboard Area */}
      <main className="flex-1 flex overflow-hidden">
        
        {/* LEFT PANEL: User Input */}
        <div className="w-1/4 flex flex-col border-r border-gray-700 bg-gray-800">
          <div className="p-4 bg-gray-700 font-semibold border-b border-gray-600">
            1. Paste Conflicted Code
          </div>
          <textarea 
            className="flex-1 w-full p-4 bg-gray-800 text-gray-300 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
            placeholder="<<<<<<< HEAD\n...\n=======\n...\n>>>>>>> incoming"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
          />
          <div className="p-4 border-t border-gray-700">
            <button 
              onClick={handleResolveClick}
              className="w-full py-2 bg-blue-600 hover:bg-blue-500 rounded text-white font-bold transition-colors"
            >
              Analyze & Resolve
            </button>
          </div>
        </div>

{/* CENTER PANEL: React Flow Graph Area */}
        <div className="w-2/4 flex flex-col bg-gray-900 relative">
          <div className="p-4 bg-gray-800 font-semibold border-b border-gray-700 absolute top-0 left-0 w-full z-10">
            2. Impact Graph (Blast Radius)
          </div>
          
          {/* NEW: The Interactive Canvas */}
          <div className="flex-1 w-full h-full border-r border-gray-700 pt-16">
            <ReactFlow nodes={nodes} edges={edges} fitView>
              <Background color="#4b5563" gap={16} />
              <Controls />
            </ReactFlow>
          </div>
        </div>

        {/* RIGHT PANEL: AI Resolution Output */}
        <div className="w-1/4 flex flex-col bg-gray-800">
          <div className="p-4 bg-gray-700 font-semibold border-b border-gray-600">
            3. Safely Merged Code
          </div>
          <textarea 
            className="flex-1 w-full p-4 bg-gray-800 text-green-400 resize-none focus:outline-none font-mono text-sm"
            readOnly
            placeholder="// Merged code will appear here..."
            value={resolvedText}
          />
        </div>

      </main>
    </div>
  )
}

export default App