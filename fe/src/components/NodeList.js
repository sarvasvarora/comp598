import axios from 'axios';
import { useState, useEffect } from 'react'

axios.defaults.headers.post['Content-Type'] ='application/json;charset=utf-8';
axios.defaults.headers.post['Access-Control-Allow-Origin'] = '*';

const NodeList = ({ props }) => {

  const RM_HOST = props.host;
  const RM_PORT = props.port;

  const [nodes, setNodes] = useState(new Map());
  const [pods, setPods] = useState(new Map());

  const [pod0Usage, setPod0Usage] = useState([]);
  const [pod1Usage, setPod1Usage] = useState([]);
  const [pod2Usage, setPod2Usage] = useState([]);

  const id_to_state = new Map([
    ['pod_0', pod0Usage],
    ['pod_1', pod1Usage],
    ['pod_2', pod2Usage]
  ]);

  // grab nodes
  useEffect(() => {
    axios.get(`http://${RM_HOST}:${RM_PORT}/nodes`)
      .then(res => {
        setNodes(res.data['Nodes'].reduce((m, node) => m.set(Object.keys(res.data['Nodes'][m.size])[0], Object.values(node)[0]), new Map()))
      })
  }, [])

  // grab pods
  useEffect(() => {
    axios.get(`http://${RM_HOST}:${RM_PORT}/pods`)
      .then(res => {
        setPods(res.data['Pods'].reduce((m, pod) => m.set(Object.keys(res.data['Pods'][m.size])[0], Object.values(pod)[0]), new Map()))
      })
  }, [])

  // grab pods
  useEffect(() => {
    axios.get(`http://${RM_HOST}:${RM_PORT}/elasticity/pods/pod_0`)
      .then(res => {
        setPod0Usage([res.data.pod_info.cpu_percentage, res.data.pod_info.mem_percentage])
        console.log([res.data.pod_info.cpu_percentage, res.data.pod_info.mem_percentage])
      })
    axios.get(`http://${RM_HOST}:${RM_PORT}/elasticity/pods/pod_1`)
      .then(res => {
        setPod1Usage([res.data.pod_info.cpu_percentage, res.data.pod_info.mem_percentage])
        console.log([res.data.pod_info.cpu_percentage, res.data.pod_info.mem_percentage])
      })
    axios.get(`http://${RM_HOST}:${RM_PORT}/elasticity/pods/pod_2`)
      .then(res => {
        setPod2Usage([res.data.pod_info.cpu_percentage, res.data.pod_info.mem_percentage])
        console.log([res.data.pod_info.cpu_percentage, res.data.pod_info.mem_percentage])
      })
    }
  , [])


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
        <h2>{pods.get(podId).name}</h2>
        <p>Avg CPU Usage (% of container limit): {id_to_state.get(podId)[0]}</p>
        <p>Avg Memory Usage (% of container limit): {id_to_state.get(podId)[1]}</p>
        <ul>{renderNodes(podId)}</ul>
      </div>
    )
  }

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