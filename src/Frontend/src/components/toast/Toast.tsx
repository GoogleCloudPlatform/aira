import 'react-toastify/dist/ReactToastify.css';
import { ToastContainer } from "react-toastify";

const Toast : React.FC = () => {

    const toastTheme = 'dark';

    return (    
        <ToastContainer
            className="md:min-w-max"
            position="bottom-right"
            autoClose={5000}
            hideProgressBar={false}
            newestOnTop
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
            theme={toastTheme}
        />
    );
}

export default Toast;