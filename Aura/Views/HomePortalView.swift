//
//  HomePortalView.swift
//  Aura
//
//  Created by Nicholas Marcenelle on 12/16/25.
//

import SwiftUI
import AVFoundation

struct HomePortalView: View {
    @ObservedObject var session: Session
    @State private var showCamera = false
    @State private var capturedImage: UIImage?
    
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
                // Top bar
                HStack {
                    Text("AURA")
                        .font(.system(size: 24, weight: .bold, design: .rounded))
                        .foregroundColor(.white)
                    
                    Spacer()
                    
                    Image(systemName: "bell.fill")
                        .font(.system(size: 20))
                        .foregroundColor(.white)
                }
                .padding(.horizontal, 20)
                .padding(.top, 10)
                
                Spacer()
                
                // Face display area with grid overlay
                ZStack {
                    if let faceImage = session.faceImage {
                        Image(uiImage: faceImage)
                            .resizable()
                            .scaledToFit()
                            .frame(maxWidth: .infinity, maxHeight: 400)
                            .clipShape(RoundedRectangle(cornerRadius: 20))
                            .overlay(
                                // Grid overlay effect
                                GridOverlay()
                            )
                    } else {
                        // Placeholder
                        RoundedRectangle(cornerRadius: 20)
                            .fill(Color.white.opacity(0.1))
                            .frame(height: 400)
                            .overlay(
                                VStack(spacing: 16) {
                                    Image(systemName: "face.smiling")
                                        .font(.system(size: 60))
                                        .foregroundColor(.white.opacity(0.6))
                                    Text("Position your face here")
                                        .font(.system(size: 16, weight: .medium))
                                        .foregroundColor(.white.opacity(0.8))
                                }
                            )
                            .overlay(
                                GridOverlay()
                            )
                    }
                }
                .padding(.horizontal, 20)
                
                Spacer()
                
                // Start Session Button
                Button(action: {
                    showCamera = true
                }) {
                    Text("Start Session")
                        .font(.system(size: 20, weight: .semibold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .frame(height: 56)
                        .background(
                            // Liquid glass effect
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
                .padding(.bottom, 20)
                
                // Quick options
                HStack(spacing: 16) {
                    QuickOptionButton(
                        icon: "sun.max.fill",
                        title: "Morning Rush",
                        action: {
                            // Quick start with preset
                            startQuickSession(preset: .morningRush)
                        }
                    )
                    
                    QuickOptionButton(
                        icon: "briefcase.fill",
                        title: "The Professional",
                        action: {
                            startQuickSession(preset: .professional)
                        }
                    )
                    
                    QuickOptionButton(
                        icon: "wineglass.fill",
                        title: "Evening Glam",
                        action: {
                            startQuickSession(preset: .eveningGlam)
                        }
                    )
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 40)
            }
        }
        .sheet(isPresented: $showCamera) {
            CameraView(capturedImage: $capturedImage)
        }
        .onChange(of: capturedImage) { newImage in
            if let image = newImage {
                session.faceImage = image
                session.state = .intake
            }
        }
    }
    
    private func startQuickSession(preset: QuickPreset) {
        // Set quick preset values
        switch preset {
        case .morningRush:
            session.occasion = .office
            session.glamLevel = GlamLevel(value: 0.3)
            session.goals = [.glowySkin]
        case .professional:
            session.occasion = .office
            session.glamLevel = GlamLevel(value: 0.4)
            session.goals = [.glowySkin, .definedLips]
        case .eveningGlam:
            session.occasion = .party
            session.glamLevel = GlamLevel(value: 0.8)
            session.goals = [.boldEye, .definedLips]
        }
        
        if session.faceImage != nil {
            session.state = .intake
        } else {
            showCamera = true
        }
    }
}

enum QuickPreset {
    case morningRush
    case professional
    case eveningGlam
}

struct QuickOptionButton: View {
    let icon: String
    let title: String
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 24))
                    .foregroundColor(.white)
                
                Text(title)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.white.opacity(0.9))
            }
            .frame(maxWidth: .infinity)
            .frame(height: 80)
            .background(
                ZStack {
                    RoundedRectangle(cornerRadius: 16)
                        .fill(.ultraThinMaterial)
                    
                    RoundedRectangle(cornerRadius: 16)
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
                RoundedRectangle(cornerRadius: 16)
                    .stroke(Color.white.opacity(0.2), lineWidth: 1)
            )
        }
    }
}

struct GridOverlay: View {
    var body: some View {
        GeometryReader { geometry in
            Path { path in
                let spacing: CGFloat = 30
                let rows = Int(geometry.size.height / spacing)
                let cols = Int(geometry.size.width / spacing)
                
                // Vertical lines
                for i in 0...cols {
                    let x = CGFloat(i) * spacing
                    path.move(to: CGPoint(x: x, y: 0))
                    path.addLine(to: CGPoint(x: x, y: geometry.size.height))
                }
                
                // Horizontal lines
                for i in 0...rows {
                    let y = CGFloat(i) * spacing
                    path.move(to: CGPoint(x: 0, y: y))
                    path.addLine(to: CGPoint(x: geometry.size.width, y: y))
                }
            }
            .stroke(Color.white.opacity(0.3), lineWidth: 0.5)
            
            // Dots at intersections
            ForEach(0..<(rows * cols), id: \.self) { index in
                let row = index / cols
                let col = index % cols
                Circle()
                    .fill(Color.white.opacity(0.4))
                    .frame(width: 4, height: 4)
                    .position(
                        x: CGFloat(col) * spacing,
                        y: CGFloat(row) * spacing
                    )
            }
        }
    }
}

#Preview {
    HomePortalView(session: Session())
}

