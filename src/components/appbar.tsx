import ThemeToggler from "./themeToggler";
import UserAccountButton from "./userAvatar";



 export default function AppBar (props:any){

return(
<section>
<div className="flex justify-between px-5">
<h1 className="appbar_title">W.T.C SASL</h1>
<div className="flex gap-2">
    <UserAccountButton/>
    
      <ThemeToggler/>
</div>

</div>

{props.children}
</section>
);



}

