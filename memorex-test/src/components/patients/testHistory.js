import React from "react";
import { useState, useEffect } from "react";
import { useNavigate, Link, useLocation } from "react-router-dom";
import classes from "../account.module.css";
import axios from "axios";
import { Amplify, Auth, Hub } from "aws-amplify";

export default function TestHistory() {
  const loc = useLocation();
  const pk = loc.state.PK.split("#");
  const sk = loc.state.SK.split("#");
  const [patient, setPatient] = useState();
  const [tests, setTests] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const [testImage, setTestImage] = useState("");

  let navigate = useNavigate();
  useEffect(() => {
    getSession();
  }, []);

  async function getSession() {
    try {
      const session = await Auth.currentSession();
    } catch {
      let path = "/accessDenied";
      navigate(path);
    }
    const session = await Auth.currentSession();
    const patientResponse = await axios.get(`/${pk[0]}/${pk[1]}/${sk[0]}/${sk[1]}`, { params: {
      idToken: session.accessToken.jwtToken
    }});
    setPatient(patientResponse.data.Item);
    setTests(patientResponse.data.Item.tests);
    setLoaded(true);
  }

  async function showTest(testId) {
    const session = await Auth.currentSession();
    let fileName = sk[1] + '-' + testId
    let testImage = await axios.get(`/getTestResults/${fileName}`, { params: {
      idToken: session.accessToken.jwtToken
    }});
    console.log(testImage);
    setTestImage(testImage.data);
  }

  return (
    <div>
      {loaded && (
        <div>
          <div className={classes.accountwrapper}>
            <h1 className={classes.title}>
              {patient.firstName} {patient.lastName}
            </h1>
          </div>
          <img src={testImage} alt="testImage" />
          <table className={classes.tableWrapper}>
            <thead>
              <tr>
                <th>Date Sent</th>
                <th>Status</th>
                <th>Score</th>
                <th>Test</th>
              </tr>
            </thead>
            <tbody>
              {tests.map((test) => {
                return (
                  <tr key={test.dateSent}>
                    <td>{test.dateSent}</td>
                    <td>{test.status}</td>
                    <td>{test.result}</td>
                    <td>
                      <button onClick={() => showTest(test.testId)}>View Test</button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
