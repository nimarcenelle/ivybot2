//
//  ContentView.swift
//  Aura
//
//  Created by Nicholas Marcenelle on 12/16/25.
//

import SwiftUI

struct ContentView: View {
    @StateObject private var session = Session()
    
    var body: some View {
        ZStack {
            switch session.state {
            case .home, .scanning:
                HomePortalView(session: session)
            case .intake:
                IntakeBriefView(session: session)
            case .generating:
                if session.generatedLookImage == nil {
                    RevealView(session: session)
                } else {
                    RevealView(session: session)
                }
            case .reveal:
                RevealView(session: session)
            case .tutorial:
                TutorialView(session: session)
            case .finished:
                FinishLineView(session: session)
            }
        }
        .onAppear {
            // Reset session on app launch
            session.reset()
        }
    }
}

#Preview {
    ContentView()
}
