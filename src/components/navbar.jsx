import { useState } from "react";
import '../styles/css/navbar.css'

const Navbar = () => {
    const [isOpen, setIsOpen] = useState(false);

    const toggleMenu = () => {
        setIsOpen(!isOpen);
    };

    return (
        <nav className="navbar">
            <div className="nav-bar-container">
                <a href="/" classname = "navbar-logo">WTC SASL</a>
               <div className={`nav-menu ${isOpen ? 'active' : ''}`}>
                    <a href="/" className="nav-link" onClick={toggleMenu}>Home</a>
                    <a href="/about" className="nav-link" onClick={toggleMenu}>About</a>
                    <a href="/privacy" className="nav-link" onClick={toggleMenu}>Privacy Policy</a>
                     <a href="/app" className="nav-link" onClick={toggleMenu}>App</a>
                </div>
            </div>

            <div className="hamburger" onClick={toggleMenu}>
                <span className="bar"></span>
                <span className="bar"></span>
                <span className="bar"></span>
            </div>
        </nav>
    );
};

export default Navbar;