import logo from './logo.svg';
// import './App.css';
import NodeList from './components/NodeList';

const RM_HOST = 'localhost';
const RM_PORT = '8000';

function App() {

  return (
    <div className="App">
      <NodeList props={{ host: RM_HOST, port: RM_PORT }}/>
    </div>
  );
}

export default App;