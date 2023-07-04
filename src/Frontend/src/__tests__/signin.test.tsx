// Copyright 2022 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
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