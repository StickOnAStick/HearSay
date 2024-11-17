'use client';
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import React from 'react';
import PocketBase from 'pocketbase';

const pb = new PocketBase(process.env.NEXT_PUBLIC_LOCAL_POCKETBASE_URL);

const AuthForm: React.FC = () => {

    const router = useRouter();

    const [email, setEmail] = useState<string>('');
    const [password, setPassword] = useState<string>('');
    const [error, setError] = useState<string>(''); // Just the error message
    const [isSignUp, setIsSignUp] = useState<boolean>(false);

    const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        console.log(process.env.NEXT_PUBLIC_LOCAL_POCKETBASE_URL);
        console.log("email: ", email, " pass: ", password)
        try {
            if (isSignUp){
                await pb.collection('users').create({
                    email,
                    password,
                    passwordConfirm: password,
                });
                console.log("User registered successfully");
            } else {
                await pb.admins.authWithPassword(email, password);
                console.log("Auth Store: ", pb.authStore.model);
            }
            document.cookie = pb.authStore.exportToCookie({
                path: '/',
                secure: process.env.NODE_ENV === "production",
                httpOnly: false,
            })
            router.push('/label');

        } catch (err: unknown) {
            console.error(err);
            //@ts-expect-error Annoying type to find
            setError(err.message || "An error occured");
        }
    }


    return (
        <div className="max-w-sm mx-auto p-4 border border-white border-opacity-10 rounded-lg shadow">
            <h2 className="text-lg font-bold mb-4">{isSignUp ? 'Sign Up' : 'Sign In'}</h2>
            <form onSubmit={handleSubmit}>
                <div className="mb-4">
                    <label htmlFor="email" className="block mb-2 opacity-50">Email:</label>
                    <input
                        type="email"
                        id="email"
                        className="w-full px-3 py-2 border rounded-md text-black"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                </div>
                <div className="mb-4">
                    <label htmlFor="password" className="block mb-2 opacity-50">Password:</label>
                    <input
                        type="password"
                        id="password"
                        className="w-full px-3 py-2 border rounded text-black"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>
                {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
                <button
                    type="submit"
                    className="w-full bg-blue-500 text-white py-2 rounded-md hover:bg-blue-800 mb-6"
                >
                    {isSignUp ? 'Sign Up' : 'Sign In'}
                </button>
            </form>
            <button
                onClick={() => {
                    setIsSignUp(!isSignUp);
                    setError(''); // Clear errors when toggling
                }}
                className="w-full text-blue-500 underline opacity-70"
            >
                {isSignUp ? 'Already have an account? Sign In' : 'Don’t have an account? Sign Up'}
            </button>
        </div>
    );

}   

export default AuthForm;