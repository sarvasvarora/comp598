import axios from 'axios';
import { useState, useEffect } from 'react'

axios.defaults.headers.post['Content-Type'] ='application/json;charset=utf-8';
axios.defaults.headers.post['Access-Control-Allow-Origin'] = '*';

const RequestDashboard = ({ props }) => {

  const LOAD_BALANCER_HOST = props.host;
  const LOAD_BALANCER_PORT = props.port;

  const [requests, setRequests] = useState(new Map());

  // grab nodes
  useEffect(() => {
    axios.get(`http://${LOAD_BALANCER_HOST}:${LOAD_BALANCER_PORT}/cloud/requests/throughput`)
      .then(res => {
        console.log(res.data['heavy'])
        // console.log(new Map().set('heavy', res.data['heavy'][0]).set('medium', res.data['medium'][0]).set('light', res.data['light'][0]))
        setRequests(new Map().set('heavy', res.data['heavy']).set('medium', res.data['medium']).set('light', res.data['light']))
      })
  }, [])

  const renderRequests = () => {
    let res = []
    for(let [k, v] of requests) {
      const totalRequests = v.reduce((acc, x) => acc += x['totalRequests'], 0)
      res.push(
        <div>
          <h3>{k}</h3>
          <p>Total requests: {totalRequests}</p>
        </div>
      )
    }
    return res
  }

  return (
    <div>
      <h1> Requests </h1>
      {renderRequests()}
    </div>
  );
}



export default RequestDashboard;