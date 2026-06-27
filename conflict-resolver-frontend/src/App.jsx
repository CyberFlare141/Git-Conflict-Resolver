import { useState } from 'react'
import axios from 'axios'
import ReactFlow , { Background, Controls } from 'reactflow'
import 'reactflow/dist/style.css'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function App() {
  const [inputText , setInputText] = useState('');
  const [resolvedText , setResolvedText] = useState('');
  const [explanation , setExplanation] = useState('');
  const [confidence , setConfidence] = useState('');
  const [needsManualReview , setNeedsManualReview] = useState(false);
  const [errorMessage , setErrorMessage] = useState('');
  const [isResolving , setIsResolving] = useState(false);
  const [nodes , setNodes] = useState([]);
  const [edges , setEdges] = useState([]);

  const handleResolveClick = async () => {
    if (!inputText.trim() || isResolving) return;

    try {
      setIsResolving(true);
      setErrorMessage('');
      setExplanation('');

      const response = await axios.post(`${API_BASE_URL}/api/resolve`, {
        raw_text: inputText
      });

      const graphData = response.data.graph_data || response.data.dummy_graph_data;
      setResolvedText(response.data.ai_resolution || response.data.dummy_ai_resolution);
      setExplanation(response.data.explanation || '');
      setConfidence(response.data.confidence || '');
      setNeedsManualReview(Boolean(response.data.needs_manual_review));

      const flowNodes = graphData.nodes.map((node, index) => ({
        id: node.id,
        data: { label: node.label },
        position: { x: 240, y: index * 120 + 90 },
        className: node.type === 'conflict' ? 'flow-node flow-node-conflict' : 'flow-node flow-node-dependency'
      }));

      const flowEdges = graphData.edges.map(edge => ({
        id: `${edge.source}-${edge.target}`,
        source: edge.source,
        target: edge.target,
        animated: true,
        className: 'impact-edge'
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);

    } catch (error) {
      console.error("Error during API call:", error);
      setErrorMessage("Unable to resolve this conflict right now. Check that the backend is running, then try again.");
      setResolvedText("// Error: Unable to resolve conflict. Please check the backend and try again.");
      setConfidence('');
      setNeedsManualReview(true);
    } finally {
      setIsResolving(false);
    }

  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Git Conflict Resolver & Impact Simulator</h1>
        <p>Paste a Git conflict, inspect the impact graph, and generate a safer merged version.</p>
      </header>

      <main className="dashboard">
        <section className="panel">
          <div className="panel-title">1. Paste Conflicted Code</div>
          <textarea 
            className="code-box"
            placeholder="<<<<<<< HEAD\n...\n=======\n...\n>>>>>>> incoming"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
          />
          <div className="panel-actions">
            <button 
              onClick={handleResolveClick}
              className="primary-button"
              disabled={!inputText.trim() || isResolving}
            >
              {isResolving ? 'Resolving...' : 'Analyze & Resolve'}
            </button>
          </div>
        </section>

        <section className="panel graph-panel">
          <div className="panel-title">2. Impact Graph</div>
          <div className="graph-canvas">
            <ReactFlow nodes={nodes} edges={edges} fitView>
              <Background color="#4b5563" gap={16} />
              <Controls />
            </ReactFlow>
          </div>
        </section>

        <section className="panel result-panel">
          <div className="panel-title">3. Safely Merged Code</div>
          {errorMessage && <div className="status-message status-error">{errorMessage}</div>}
          {(explanation || confidence) && (
            <div className={`status-message ${needsManualReview ? 'status-warning' : 'status-ok'}`}>
              {confidence && <span className="status-pill">{confidence.toUpperCase()}</span>}
              <span>{explanation}</span>
            </div>
          )}
          <textarea 
            className="code-box output-box"
            readOnly
            placeholder="// Merged code will appear here..."
            value={resolvedText}
          />
        </section>

      </main>
    </div>
  )
}

export default App
