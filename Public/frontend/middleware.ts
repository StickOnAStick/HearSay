import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import PocketBase from 'pocketbase';

// Initialize PocketBase
const pb = new PocketBase(process.env.NEXT_PUBLIC_POCKETBASE_URL);

export function middleware(req: NextRequest) {
    const url = req.nextUrl.clone();
    const authCookie = req.cookies.get('pb_auth')?.value; // Assuming the authStore token is stored here
    //console.log("auth cookie: ", authCookie);
    // If the auth cookie is missing, redirect to the login page
    if (!authCookie) {
        url.pathname = '/';
        return NextResponse.redirect(url);
    }

    const parsedAuth = JSON.parse(authCookie);
    const serializedCookie = `pb_auth=${JSON.stringify({
        token: parsedAuth.token,
        model: parsedAuth.model,
    })}`;    
    //console.log('Serialized Cookie:', serializedCookie);

    try {
        pb.authStore.loadFromCookie(serializedCookie);
        //console.log("pb authstore: ", pb.authStore)
        // Verify the token
        if (!pb.authStore.isValid) {
            url.pathname = '/';
            return NextResponse.redirect(url);
        }
    } catch (error) {
        console.error('Authentication error:', error);
        url.pathname = '/';
        return NextResponse.redirect(url);
    }

    // Allow access
    return NextResponse.next();
}

// Apply middleware to protected routes
export const config = {
    matcher: ['/label'], // Protect /label or any other protected routes
};
