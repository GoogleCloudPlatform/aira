// __tests__/signin.test.jsx
import '@testing-library/jest-dom';
import { act } from 'react-dom/test-utils';
import { render, screen, waitFor } from '@testing-library/react';
import { SignIn } from '@/components';

describe('SignIn', () => {
    beforeEach(async () => {
        await act(() => {
            render(<SignIn />)
        })
    })

    it('should render form', async () => {
        await waitFor(() => {
            const form = screen.getByRole('form');
            expect(form).toBeInTheDocument();
        });
    })

    it('should render google signin button', async () => {
        await waitFor(() => {
            const googleSignIn = screen.getByTestId('google_signin');
            expect(googleSignIn).toBeInTheDocument();
        });
    })
});