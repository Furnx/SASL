import { UserRound } from "lucide-react";
import { useState } from "react";




export default function UserAccountButton (){
    const [loggedin,setloggedin] = useState(false);
    const [img,setImg] = useState("")

    return (
        <div className="accBtn">
            {loggedin? <img src={img}/>:<UserRound/>}
        </div>
    );
}