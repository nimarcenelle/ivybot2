//
//  RevealView.swift
//  Aura
//
//  Created by Nicholas Marcenelle on 12/16/25.
//

import SwiftUI

struct RevealView: View {
    @ObservedObject var session: Session
    
    var body: some View {
        ZStack {
            // Background gradient
            LinearGradient(
                colors: [Color.black.opacity(0.9), Color.purple.opacity(0.3)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
            
            VStack(spacing: 0) {
                Spacer()
                
                // Generated look image
                if let lookImage = session.generatedLookImage {
                    Image(uiImage: lookImage)
                        .resizable()
                        .scaledToFit()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .clipShape(RoundedRectangle(cornerRadius: 0))
                } else {
                    // Placeholder
                    RoundedRectangle(cornerRadius: 20)
                        .fill(Color.white.opacity(0.1))
                        .frame(maxHeight: 500)
                        .overlay(
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        )
                        .padding(.horizontal, 20)
                }
                
                Spacer()
                
                // Description box
                VStack(alignment: .leading, spacing: 12) {
                    if let description = session.generatedLookDescription {
                        Text(description)
                            .font(.system(size: 16, weight: .medium))
                            .foregroundColor(.white)
                            .multilineTextAlignment(.leading)
                    } else {
                        Text("Your personalized look is being generated...")
                            .font(.system(size: 16, weight: .medium))
                            .foregroundColor(.white.opacity(0.7))
                    }
                }
                .padding(20)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(
                    ZStack {
                        RoundedRectangle(cornerRadius: 20)
                            .fill(.ultraThinMaterial)
                        
                        RoundedRectangle(cornerRadius: 20)
                            .fill(
                                LinearGradient(
                                    colors: [Color.white.opacity(0.2), Color.white.opacity(0.1)],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                    }
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 20)
                        .stroke(Color.white.opacity(0.3), lineWidth: 1)
                )
                .padding(.horizontal, 20)
                .padding(.bottom, 20)
                
                // Start Tutorial button
                Button(action: {
                    startTutorial()
                }) {
                    HStack {
                        if session.state == .generating {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        } else {
                            Text("Start GRWM Tutorial")
                                .font(.system(size: 18, weight: .semibold))
                        }
                    }
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .frame(height: 56)
                    .background(
                        ZStack {
                            RoundedRectangle(cornerRadius: 16)
                                .fill(.ultraThinMaterial)
                            
                            RoundedRectangle(cornerRadius: 16)
                                .fill(
                                    LinearGradient(
                                        colors: [Color.white.opacity(0.2), Color.white.opacity(0.05)],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                        }
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: 16)
                            .stroke(Color.white.opacity(0.3), lineWidth: 1)
                    )
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 40)
                .disabled(session.state == .generating || session.generatedLookImage == nil)
                .opacity((session.state == .generating || session.generatedLookImage == nil) ? 0.5 : 1.0)
            }
        }
    }
    
    private func startTutorial() {
        guard let occasion = session.occasion else { return }
        
        session.state = .generating
        
        Task {
            do {
                let steps = try await GeminiService.shared.generateTutorial(
                    occasion: occasion,
                    customOccasion: session.customOccasion,
                    glamLevel: session.glamLevel,
                    goals: session.goals,
                    outfitColors: session.outfitColors
                )
                
                await MainActor.run {
                    session.tutorialSteps = steps
                    session.currentStepIndex = 0
                    session.state = .tutorial
                }
            } catch {
                await MainActor.run {
                    session.state = .reveal
                    // Handle error
                }
            }
        }
    }
}

#Preview {
    RevealView(session: Session())
}

