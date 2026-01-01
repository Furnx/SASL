import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";



export default  function ThemeToggler(){
const [lightTheme,setLightTheme] = useState<boolean>(true);
const [bgColour,setBgColour] =useState<string>(getComputedStyle(document.documentElement).getPropertyValue("--bg-colour"))
const [fgColour,setfgColour] =useState<string>(getComputedStyle(document.documentElement).getPropertyValue("--fg-colour"))

let thm=()=>{

let temp=bgColour
setBgColour(fgColour)
setfgColour(temp)


setLightTheme(!lightTheme)

}
useEffect(()=>{
document.documentElement.style.setProperty("--fg-colour",fgColour)
document.documentElement.style.setProperty("--bg-colour",bgColour)

},[lightTheme])



return (
    <button className="btnTheme" onClick={thm}>{lightTheme?<Sun/>:<Moon/>}</button>
);
}