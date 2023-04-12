import React from "react";
import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import axios from "axios";
import { Amplify, Auth, Hub } from "aws-amplify";
import { useNavigate, Link } from "react-router-dom";
import { MDBBtn, MDBContainer, MDBCard, MDBCardBody, MDBInput, MDBCheckbox } from "mdb-react-ui-kit";
import { useStripe, PaymentMethod } from "@stripe/react-stripe-js";

export default function FileUploadTest() {
   const [testImage, setTestImage] = useState("");
   const fileName = "test-2.png";
   useEffect(() => {
      getImage();
    }, []);
    
   async function uploadFile() {
      await axios.post("/uploadTestResult", {
         fileName
       });
   }

   async function getImage() {
      let imageResponse = await axios.get(`/getTestResults/${fileName}`);
      setTestImage(imageResponse.data);
      console.log(imageResponse.data);
   }

  

  return (
    <div>
      <img src={testImage} alt="testImage" />
      <button onClick={uploadFile}>Test</button>
    </div>
  );
}
