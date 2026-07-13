import Navbar from '../components/navbar';

export default function About(){
    return (
        <div style = {{display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100px'}}>
            <Navbar/>
            <h1>About Us</h1>
        </div>
    );
}