import axios from 'axios';
import { useState, useEffect } from 'react'

axios.defaults.headers.post['Content-Type'] ='application/json;charset=utf-8';
axios.defaults.headers.post['Access-Control-Allow-Origin'] = '*';

const NodeList = ({ props }) => {

  const RM_HOST = props.host;
  const RM_PORT = props.port;

  const [nodes, setNodes] = useState([]);

  useEffect(() => {
    console.log('fetching rm...');
    axios
      .get('http://localhost:8000/pods')
      .then(res => {
        setNodes(res.data);
        console.log(res.data)
      })
  }, [])

  return (
    <div>
      <h1> Pods </h1> {
        nodes.map((node) => 
        <div>
          <h2>{node['pod_name']}</h2>
          <ul>{renderNodes(node['nodes'])}</ul>
        </div>
        )
      }
    </div>
  );
}

const renderNodes = (nodes) => {
  const nodeNames = nodes.map((node) => {
    return <li>Node: {node.name} // Status: {node.status}</li>
  })
  return nodeNames;
}

export default NodeList;