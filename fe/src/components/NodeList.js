import axios from 'axios';
import { useState, useEffect } from 'react'

axios.defaults.headers.post['Content-Type'] ='application/json;charset=utf-8';
axios.defaults.headers.post['Access-Control-Allow-Origin'] = '*';

const NodeList = ({ props }) => {

  const RM_HOST = props.host;
  const RM_PORT = props.port;

  const [nodes, setNodes] = useState(new Map());
  const [pods, setPods] = useState(new Map());

  // grab nodes
  useEffect(() => {
    axios.get(`http://${RM_HOST}:${RM_PORT}/nodes`)
      .then(res => {
        setNodes(new Map(Object.entries(res.data['Nodes'])))
      })
  }, [])

  // grab pods
  useEffect(() => {
    axios.get(`http://${RM_HOST}:${RM_PORT}/pods`)
      .then(res => 
        setPods(res.data['Pods'].reduce((m, pod) => m.set(Object.values(pod)[0]['name'], pod), new Map()))
      )
  }, [])


  const getNodesFromPod = id => {
    var res = [];
    for(var [nodeId, val] of nodes) {
      if (val.podId == id) {
        res.push(<div>Node: {val.name} // Status: {val.status}</div>)        
      }
    }
    return res;
  }
  
  const renderNodes = id => { return getNodesFromPod(id).map(x => <li>{x}</li>) }

  const renderPod = podId => {
    return (
      <div>
        <h2>{podId}</h2>
        <ul>{renderNodes(podId)}</ul>
      </div>
    )
  }
  // console.log(renderPod("pod_0"))

  const renderPods = () => {
    var res = []
    for(var [pod, val] of pods) {
      res.push(renderPod(pod));
    }
    return res;
  }

  return (
    <div>
      <h1> Pods </h1>
      {renderPods()}
    </div>
  );
}



export default NodeList;