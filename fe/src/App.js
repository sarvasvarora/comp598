import logo from './logo.svg';
// import './App.css';
import NodeList from './components/NodeList';
import RequestDashboard from './components/RequestDashboard';

const RM_HOST = 'localhost';
const RM_PORT = '8000';

const LOAD_BALANCER_HOST = 'localhost'
const LOAD_BALANCER_PORT = '7000'

function App() {
  return (
    <div className="App">
      <NodeList props={{ host: RM_HOST, port: RM_PORT }}/>
      <RequestDashboard props={{ host: LOAD_BALANCER_HOST, port: LOAD_BALANCER_PORT }}/>
    </div>
  );
}

export default App;