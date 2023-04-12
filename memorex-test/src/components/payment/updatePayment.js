import React from "react";
import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import classes from "../account.module.css";
import axios from "axios";
import { Amplify, Auth, Hub } from "aws-amplify";
import { useNavigate, Link } from "react-router-dom";
import "./payment.css";
import {
  MDBBtn,
  MDBContainer,
  MDBCard,
  MDBCardBody,
  MDBInput,
  MDBCheckbox,
  MDBListGroup,
  MDBListGroupItem,
} from "mdb-react-ui-kit";
import Payment from "./Payment";
import "bootstrap/dist/css/bootstrap.min.css";
export default function UpdatePayment() {
  const initialFormState = {
    formType: "updatePaymentMethod",
  };

  /// Use States
  const [card, setCard] = useState([]);
  const [price, setPrice] = useState();
  const [subId, setSubId] = useState();
  const [isDisabled, setIsDisabled] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formState, updateFormState] = useState(initialFormState);
  const [cancelled, setCancelled] = useState();
  const [defaultCard, setDefaultCard] = useState();
  const [productName, setProductName] = useState();

  const { formType } = formState;

  /// navigate method called
  let navigate = useNavigate();

  /// useEffect used to load the getSession() function on page load
  useEffect(() => {
    getSession();
  }, []);

  ///Various information is called in this function. Information from DynamoDB, Stripe and Cognito.
  async function reloadPage() {
    /// Loading is set to true while data is being fetched.
    setLoading(true);
    const session = await Auth.currentSession();

    ///The Form State is set to the update payment method page.
    updateFormState(() => ({ ...formState, formType: "updatePaymentMethod" }));

    ///A GET method is sent through axios that takes in the current session's email to receive information about a Stripe Customer.
    const myCustomer = await axios.get(`/showCustomer/${session.idToken.payload.email}`, {
      params: {
        idToken: session.accessToken.jwtToken,
      },
    });

    ///Attribute for the default payment method that a customer has set.
    ///Later used to compare the selected card id to the current default payment method.
    setDefaultCard(myCustomer.data.data[0].invoice_settings.default_payment_method);

    ///A GET method is sent through axios that takes in the current session's email to receive payment information about a Stripe Customer.
    const myPayment = await axios.get(`/showPayment/${session.idToken.payload.email}`, {
      params: {
        idToken: session.accessToken.jwtToken,
      },
    });

    ///A list of payment methods that the customer owns is returned and is set through setCard();
    setCard(myPayment.data.data);

    ///A GET method is sent through axios that takes in
    ///the current session's email to receive the current product information associated with the customer.
    const myCurrentProduct = await axios.get(`/currentProduct/${session.idToken.payload.email}`, {
      params: {
        idToken: session.accessToken.jwtToken,
      },
    });

    ///The product name is set and called in the html.
    setProductName(myCurrentProduct.data.name);

    ///A GET method is sent through axios that takes in
    ///the current session's email to receive the current subscription information.
    const mySubscription = await axios.get(`/currentSubscription/${session.idToken.payload.email}/""`, {
      params: {
        idToken: session.accessToken.jwtToken,
      },
    });
    console.log(mySubscription);

    ///A list of the subscriptions is checked to see if any of them are active and if so, checks to see if any
    ///are set to be canceled at the end of the subscription period end. the "canceled" useState is set to false if
    ///a subscription is being canceled and true if it is not. The canceled variable is used to decided what button is being shown.
    for (let i = 0; i < mySubscription.data.data.length; i++) {
      console.log(mySubscription.data.data[i].id);
      console.log(mySubscription.data.data[i].status);
      if (mySubscription.data.data[i].status === "active") {
        console.log(mySubscription.data.data[i].cancel_at_period_end);
        if (mySubscription.data.data[i].cancel_at_period_end === false) {
          setCancelled(false);
        } else if (mySubscription.data.data[i].cancel_at_period_end === true) {
          setCancelled(true);
        }
      }
    }

    ///Depending on what the current subscription is, the subId is set accordingly on the radio buttons on page load.
    if (myCurrentProduct.data.name === "Monthly") {
      setSubId("1");
    } else if (myCurrentProduct.data.name === "Half-year") {
      setSubId("2");
    } else if (myCurrentProduct.data.name === "Yearly") {
      setSubId("3");
    }

    /// Loading is set to false once data is done being fetched.
    setLoading(false);
  }

  /// this function checks if a session exists and redirects the user to an "accessed denied" page if a session is not found.
  /// The reloadPage function is called at the end to re fetch data.
  async function getSession() {
    try {
      const session = await Auth.currentSession();
    } catch {
      let path = "/accessDenied";
      navigate(path);
    }
    reloadPage();
  }

  ///When the select button is clicked, the function takes in an ID parameter of the specific card who's button was clicked.
  ///A GET method is sent through axios that takes in the current session's email and the selected card's id, a default card
  ///is then selected through the python backend.
  async function onSelectCard(cardId) {
    const session = await Auth.currentSession();
    await axios.get(`/setDefaultCard/${session.idToken.payload.email}/${cardId}`);
    reloadPage();
  }

  ///When a radio button is clicked, the subId is set to which subscription type was chosen.
  function onChange(e) {
    if (e.target.value === "1") {
      setSubId("1");
    } else if (e.target.value === "2") {
      setSubId("2");
    } else if (e.target.value === "3") {
      setSubId("3");
    }
  }

  ///
  async function onDelete(cardId) {
    setLoading(true);
    const session = await Auth.currentSession();
    await axios.get(`/showPayment/${session.idToken.payload.email}`, {
      params: {
        idToken: session.accessToken.jwtToken,
      },
    });
    const myCustomer = await axios.get(`/showCustomer/${session.idToken.payload.email}`, {
      params: {
        idToken: session.accessToken.jwtToken,
      },
    });
    const mySubscription = await axios.get(`/currentSubscription/${session.idToken.payload.email}/""`, {
      params: {
        idToken: session.accessToken.jwtToken,
      },
    });
    if (myCustomer.data.data[0].invoice_settings.default_payment_method !== cardId) {
      await axios.get(`/deletePaymentMethod/${cardId}`, {
        params: {
          idToken: session.accessToken.jwtToken,
        },
      });
      reloadPage();
    } else {
      for (let i = 0; i < mySubscription.data.data.length; i++) {
        if (mySubscription.data.data[i].status === "active") {
          alert("You have an ongoing subscription");
        } else {
          await axios.get(`/deletePaymentMethod/${cardId}`, {
            params: {
              idToken: session.accessToken.jwtToken,
            },
          });
          reloadPage();
        }
      }
    }
  }

  async function Subscription(buttonType) {
    setLoading(true);
    const session = await Auth.currentSession();
    if (buttonType === "Update") {
      await axios.get(`updateSubscription/${session.idToken.payload.email}/${subId}`, {
        params: {
          idToken: session.accessToken.jwtToken,
        },
      });
    } else {
      await axios.get(`/currentSubscription/${session.idToken.payload.email}/${buttonType}`, {
        params: {
          idToken: session.accessToken.jwtToken,
        },
      });
    }
    reloadPage();
  }

  return (
    <div>
      {loading ? (
        <h1>Loading Payment Information...</h1>
      ) : (
        <div>
          {formType === "updatePaymentMethod" && (
            <div>
              <p>Card Information</p>
              {card.map((myCard) => {
                return (
                  <MDBContainer>
                    <MDBCard>
                      <MDBCardBody>
                        <div>
                          <ul key={myCard.id}>
                            <li>{myCard.billing_details.name}</li>
                            <li>**** **** **** {myCard.card.last4}</li>
                            <li>{myCard.card.brand}</li>
                            <li>{myCard.card.date}</li>
                            <li>
                              <div className="centered-buttons">
                                <MDBBtn class="btn btn-primary btn-sm mr-2" onClick={() => onSelectCard(myCard.id)}>
                                  {defaultCard === myCard.id ? "Selected" : "Select"}
                                </MDBBtn>
                                <MDBBtn class="btn btn-primary btn-sm ml-2" onClick={() => onDelete(myCard.id)}>
                                  Delete
                                </MDBBtn>
                              </div>
                            </li>
                          </ul>
                        </div>
                      </MDBCardBody>
                    </MDBCard>
                  </MDBContainer>
                );
              })}
              <MDBContainer>
                <MDBCard>
                  <MDBCardBody>
                    <MDBBtn
                      class="btn btn-primary btn-sm"
                      onClick={() =>
                        updateFormState(() => ({
                          ...formState,
                          formType: "addPayment",
                        }))
                      }
                    >
                      Add Payment Method
                    </MDBBtn>
                    <p>Current Subscription</p>
                    <p>{productName}</p>
                    <div className="register-radio">
                      <input
                        name="subscription"
                        id="1"
                        onChange={onChange}
                        wrapperClass="mb-3"
                        type="radio"
                        value="1"
                        checked={subId === "1"}
                      />
                      <label className="text-center mb-2" htmlFor="1">
                        1 Month $150
                      </label>
                      <input
                        name="subscription"
                        id="2"
                        onChange={onChange}
                        wrapperClass="mb-3"
                        type="radio"
                        value="2"
                        checked={subId === "2"}
                      />
                      <label className="text-center mb-2" htmlFor="2">
                        6 Months $900
                      </label>
                      <input
                        name="subscription"
                        id="3"
                        onChange={onChange}
                        wrapperClass="mb-3"
                        type="radio"
                        value="3"
                        checked={subId === "3"}
                      />
                      <label className="text-center mb-2" htmlFor="3">
                        12 Months $1800
                      </label>
                    </div>
                    <div className="centered-buttons">
                      <MDBBtn onClick={() => Subscription("Update")}>Update Subscription</MDBBtn>
                      {cancelled ? (
                        <MDBBtn onClick={() => Subscription("Resume")}>Resume Subscription</MDBBtn>
                      ) : (
                        <MDBBtn onClick={() => Subscription("Cancel")}>Cancel Subscription</MDBBtn>
                      )}
                    </div>
                  </MDBCardBody>
                </MDBCard>
              </MDBContainer>
            </div>
          )}
          {formType === "addPayment" && <Payment />}
        </div>
      )}
    </div>
  );
}
