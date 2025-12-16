//
//  TutorialView.swift
//  Aura
//
//  Created by Nicholas Marcenelle on 12/16/25.
//

import SwiftUI

struct TutorialView: View {
    @ObservedObject var session: Session
    @State private var isMuted = false
    
    var currentStep: MakeupStep? {
        guard session.currentStepIndex < session.tutorialSteps.count else { return nil }
        return session.tutorialSteps[session.currentStepIndex]
    }
    
    var body: some View {
        ZStack {
            // Background with face
            ZStack {
                if let faceImage = session.faceImage {
                    Image(uiImage: faceImage)
                        .resizable()
                        .scaledToFill()
                        .blur(radius: 5)
                        .opacity(0.4)
                }
                
                LinearGradient(
                    colors: [Color.black.opacity(0.8), Color.purple.opacity(0.4)],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            }
            .ignoresSafeArea()
            
            VStack(spacing: 0) {
                // Top bar
                HStack {
                    Button(action: {
                        session.state = .reveal
                    }) {
                        Image(systemName: "chevron.left")
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundColor(.white)
                            .frame(width: 44, height: 44)
                            .background(
                                Circle()
                                    .fill(.ultraThinMaterial)
                            )
                    }
                    
                    Spacer()
                    
                    Button(action: {
                        isMuted.toggle()
                    }) {
                        Image(systemName: isMuted ? "speaker.slash.fill" : "speaker.wave.2.fill")
                            .font(.system(size: 18))
                            .foregroundColor(.white)
                            .frame(width: 44, height: 44)
                            .background(
                                Circle()
                                    .fill(.ultraThinMaterial)
                            )
                    }
                }
                .padding(.horizontal, 20)
                .padding(.top, 10)
                
                Spacer()
                
                // Face with AR guidelines overlay
                if let faceImage = session.faceImage, let step = currentStep {
                    ZStack {
                        Image(uiImage: faceImage)
                            .resizable()
                            .scaledToFit()
                            .frame(maxWidth: .infinity, maxHeight: 400)
                            .clipShape(RoundedRectangle(cornerRadius: 20))
                        
                        // AR Guidelines overlay
                        if let guidelines = step.arGuidelines {
                            ARGuidelinesOverlay(guidelines: guidelines)
                        }
                    }
                    .padding(.horizontal, 20)
                }
                
                Spacer()
                
                // Instruction box
                if let step = currentStep {
                    VStack(alignment: .leading, spacing: 16) {
                        // Step indicator
                        Text("Step \(step.stepNumber)/\(step.totalSteps)")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(.white.opacity(0.7))
                        
                        // Title
                        Text(step.title)
                            .font(.system(size: 22, weight: .bold))
                            .foregroundColor(.white)
                        
                        // Instruction
                        Text(step.instruction)
                            .font(.system(size: 16, weight: .regular))
                            .foregroundColor(.white.opacity(0.9))
                            .lineSpacing(4)
                        
                        // Product info
                        if let product = step.product {
                            HStack(spacing: 12) {
                                Image(systemName: "paintbrush.fill")
                                    .font(.system(size: 16))
                                    .foregroundColor(.white.opacity(0.8))
                                
                                Text(product)
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(.white.opacity(0.8))
                            }
                            .padding(.top, 8)
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
                }
                
                // Navigation buttons
                HStack(spacing: 16) {
                    Button(action: {
                        if session.currentStepIndex > 0 {
                            session.currentStepIndex -= 1
                        }
                    }) {
                        Text("Previous")
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: 50)
                            .background(
                                ZStack {
                                    RoundedRectangle(cornerRadius: 12)
                                        .fill(.ultraThinMaterial)
                                    
                                    RoundedRectangle(cornerRadius: 12)
                                        .fill(
                                            LinearGradient(
                                                colors: [Color.white.opacity(0.15), Color.white.opacity(0.05)],
                                                startPoint: .topLeading,
                                                endPoint: .bottomTrailing
                                            )
                                        )
                                }
                            )
                            .overlay(
                                RoundedRectangle(cornerRadius: 12)
                                    .stroke(Color.white.opacity(0.2), lineWidth: 1)
                            )
                    }
                    .disabled(session.currentStepIndex == 0)
                    .opacity(session.currentStepIndex == 0 ? 0.5 : 1.0)
                    
                    Button(action: {
                        if session.currentStepIndex < session.tutorialSteps.count - 1 {
                            session.currentStepIndex += 1
                        } else {
                            // Finished tutorial
                            session.state = .finished
                        }
                    }) {
                        Text(session.currentStepIndex < session.tutorialSteps.count - 1 ? "Next" : "Finish")
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: 50)
                            .background(
                                ZStack {
                                    RoundedRectangle(cornerRadius: 12)
                                        .fill(.ultraThinMaterial)
                                    
                                    RoundedRectangle(cornerRadius: 12)
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
                                RoundedRectangle(cornerRadius: 12)
                                    .stroke(Color.white.opacity(0.3), lineWidth: 1)
                            )
                    }
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 40)
            }
        }
    }
}

struct ARGuidelinesOverlay: View {
    let guidelines: ARGuidelines
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // Cheek contour guidelines
                if guidelines.cheekContour {
                    Path { path in
                        let centerX = geometry.size.width / 2
                        let centerY = geometry.size.height / 2
                        
                        // Left cheek
                        path.move(to: CGPoint(x: centerX * 0.3, y: centerY * 0.6))
                        path.addLine(to: CGPoint(x: centerX * 0.5, y: centerY * 0.8))
                        
                        // Right cheek
                        path.move(to: CGPoint(x: centerX * 1.7, y: centerY * 0.6))
                        path.addLine(to: CGPoint(x: centerX * 1.5, y: centerY * 0.8))
                    }
                    .stroke(Color.brown.opacity(0.6), lineWidth: 3)
                }
                
                // Forehead contour
                if guidelines.foreheadContour {
                    Path { path in
                        let centerX = geometry.size.width / 2
                        let centerY = geometry.size.height / 2
                        
                        path.move(to: CGPoint(x: centerX * 0.4, y: centerY * 0.2))
                        path.addLine(to: CGPoint(x: centerX * 1.6, y: centerY * 0.2))
                    }
                    .stroke(Color.brown.opacity(0.6), lineWidth: 3)
                }
                
                // Eye guidelines
                if guidelines.eyeGuidelines {
                    Path { path in
                        let centerX = geometry.size.width / 2
                        let centerY = geometry.size.height / 2
                        
                        // Left eye
                        path.addEllipse(in: CGRect(
                            x: centerX * 0.3,
                            y: centerY * 0.4,
                            width: centerX * 0.3,
                            height: centerY * 0.15
                        ))
                        
                        // Right eye
                        path.addEllipse(in: CGRect(
                            x: centerX * 1.4,
                            y: centerY * 0.4,
                            width: centerX * 0.3,
                            height: centerY * 0.15
                        ))
                    }
                    .stroke(Color.brown.opacity(0.6), lineWidth: 2)
                }
                
                // Lip guidelines
                if guidelines.lipGuidelines {
                    Path { path in
                        let centerX = geometry.size.width / 2
                        let centerY = geometry.size.height / 2
                        
                        path.addEllipse(in: CGRect(
                            x: centerX * 0.6,
                            y: centerY * 0.85,
                            width: centerX * 0.8,
                            height: centerY * 0.1
                        ))
                    }
                    .stroke(Color.brown.opacity(0.6), lineWidth: 2)
                }
            }
        }
    }
}

#Preview {
    TutorialView(session: Session())
}

