import { Link } from "react-router-dom";
import classes from "../navigation/navigation.module.css";
import { Amplify, Auth, Hub } from "aws-amplify";
import { useNavigate } from "react-router-dom";

export default function AccessDenied() {
  let navigate = useNavigate();
  const pageChange = () => {
    let path = "/";
    navigate(path);
  };
  // async function handleLogOut() {
  //   Auth.signOut();
  //   pageChange();
  // }

  return (
    <div>
      <h3>You do not have permission to access this page.</h3>
      <a href="/">Log in</a>
    </div>
  );
}
