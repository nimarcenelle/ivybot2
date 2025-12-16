//
//  FinishLineView.swift
//  Aura
//
//  Created by Nicholas Marcenelle on 12/16/25.
//

import SwiftUI

struct FinishLineView: View {
    @ObservedObject var session: Session
    @State private var showComparison = false
    @State private var isComparing = false
    
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
                
                // Final look image
                if let lookImage = session.generatedLookImage {
                    ZStack {
                        Image(uiImage: lookImage)
                            .resizable()
                            .scaledToFit()
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                            .clipShape(RoundedRectangle(cornerRadius: 0))
                            .opacity(showComparison ? 0.5 : 1.0)
                        
                        // Comparison overlay
                        if showComparison, let originalImage = session.faceImage {
                            Image(uiImage: originalImage)
                                .resizable()
                                .scaledToFit()
                                .frame(maxWidth: .infinity, maxHeight: .infinity)
                                .clipShape(RoundedRectangle(cornerRadius: 0))
                                .opacity(0.5)
                        }
                        
                        // Comparison button overlay
                        VStack {
                            Spacer()
                            
                            Button(action: {
                                withAnimation {
                                    isComparing.toggle()
                                    showComparison = isComparing
                                }
                            }) {
                                Text("Press and Hold to Compare")
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(.white)
                                    .padding(.horizontal, 20)
                                    .padding(.vertical, 12)
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
                            }
                            .padding(.bottom, 20)
                        }
                    }
                }
                
                Spacer()
                
                // Action buttons
                HStack(spacing: 16) {
                    ActionButton(
                        icon: "heart.fill",
                        title: "Save Look",
                        action: {
                            // Save look
                        }
                    )
                    
                    ActionButton(
                        icon: "bag.fill",
                        title: "Shop Products",
                        action: {
                            // Shop products
                        }
                    )
                    
                    ActionButton(
                        icon: "square.and.arrow.up",
                        title: "Share Video",
                        action: {
                            // Share video
                        }
                    )
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 40)
            }
        }
        .gesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in
                    if !isComparing {
                        withAnimation {
                            isComparing = true
                            showComparison = true
                        }
                    }
                }
                .onEnded { _ in
                    withAnimation {
                        isComparing = false
                        showComparison = false
                    }
                }
        )
    }
}

struct ActionButton: View {
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

#Preview {
    FinishLineView(session: Session())
}

