//
//  IntakeBriefView.swift
//  Aura
//
//  Created by Nicholas Marcenelle on 12/16/25.
//

import SwiftUI

struct IntakeBriefView: View {
    @ObservedObject var session: Session
    @State private var showColorPicker = false
    @State private var showCustomOccasionInput = false
    @State private var customOccasionText = ""
    
    var body: some View {
        ZStack {
            // Background with blurred face
            ZStack {
                if let faceImage = session.faceImage {
                    Image(uiImage: faceImage)
                        .resizable()
                        .scaledToFill()
                        .blur(radius: 20)
                        .opacity(0.3)
                }
                
                LinearGradient(
                    colors: [Color.black.opacity(0.8), Color.purple.opacity(0.4)],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            }
            .ignoresSafeArea()
            
            ScrollView {
                VStack(spacing: 32) {
                    // OCCASION Section
                    VStack(alignment: .leading, spacing: 16) {
                        Text("OCCASION")
                            .font(.system(size: 18, weight: .bold, design: .rounded))
                            .foregroundColor(.white)
                        
                        HStack(spacing: 12) {
                            ForEach([Occasion.dateNight, .office, .party]) { occasion in
                                OccasionButton(
                                    occasion: occasion,
                                    isSelected: session.occasion == occasion,
                                    action: {
                                        session.occasion = occasion
                                        session.customOccasion = nil
                                    }
                                )
                            }
                        }
                        
                        // Custom occasion option
                        Button(action: {
                            showCustomOccasionInput = true
                        }) {
                            HStack {
                                Image(systemName: "pencil")
                                    .font(.system(size: 16))
                                Text("Custom")
                                    .font(.system(size: 16, weight: .medium))
                            }
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
                                    .stroke(
                                        session.occasion == .custom ? Color.white.opacity(0.6) : Color.white.opacity(0.2),
                                        lineWidth: session.occasion == .custom ? 2 : 1
                                    )
                            )
                        }
                    }
                    .padding(.horizontal, 20)
                    .padding(.top, 20)
                    
                    // GOAL Section
                    VStack(alignment: .leading, spacing: 16) {
                        Text("GOAL")
                            .font(.system(size: 18, weight: .bold, design: .rounded))
                            .foregroundColor(.white)
                        
                        HStack(spacing: 12) {
                            ForEach([GlamGoal.glowySkin, .boldEye, .definedLips]) { goal in
                                GoalButton(
                                    goal: goal,
                                    isSelected: session.goals.contains(goal),
                                    action: {
                                        if session.goals.contains(goal) {
                                            session.goals.remove(goal)
                                        } else {
                                            session.goals.insert(goal)
                                        }
                                    }
                                )
                            }
                        }
                    }
                    .padding(.horizontal, 20)
                    
                    // GLAM LEVEL Section
                    VStack(alignment: .leading, spacing: 16) {
                        Text("GLAM GOAL")
                            .font(.system(size: 18, weight: .bold, design: .rounded))
                            .foregroundColor(.white)
                        
                        VStack(spacing: 12) {
                            HStack {
                                Text("NATURAL")
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(.white.opacity(0.7))
                                
                                Spacer()
                                
                                Text("FULL BEAT")
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(.white.opacity(0.7))
                            }
                            
                            Slider(value: $session.glamLevel.value, in: 0...1)
                                .tint(.white)
                                .background(
                                    RoundedRectangle(cornerRadius: 8)
                                        .fill(.ultraThinMaterial)
                                        .padding(.vertical, -8)
                                )
                            
                            Text(session.glamLevel.description.uppercased())
                                .font(.system(size: 16, weight: .semibold))
                                .foregroundColor(.white)
                        }
                        .padding(20)
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
                    .padding(.horizontal, 20)
                    
                    // OUTFIT COLOR Section
                    VStack(alignment: .leading, spacing: 16) {
                        Text("OUTFIT COLOR")
                            .font(.system(size: 18, weight: .bold, design: .rounded))
                            .foregroundColor(.white)
                        
                        // Selected colors display
                        if !session.outfitColors.isEmpty {
                            HStack(spacing: 12) {
                                ForEach(session.outfitColors.prefix(3)) { outfitColor in
                                    Circle()
                                        .fill(outfitColor.color)
                                        .frame(width: 50, height: 50)
                                        .overlay(
                                            Circle()
                                                .stroke(Color.white.opacity(0.3), lineWidth: 2)
                                        )
                                }
                                
                                if session.outfitColors.count < 3 {
                                    Button(action: {
                                        showColorPicker = true
                                    }) {
                                        Image(systemName: "plus")
                                            .font(.system(size: 20))
                                            .foregroundColor(.white)
                                            .frame(width: 50, height: 50)
                                            .background(
                                                Circle()
                                                    .fill(.ultraThinMaterial)
                                            )
                                            .overlay(
                                                Circle()
                                                    .stroke(Color.white.opacity(0.3), lineWidth: 2)
                                            )
                                    }
                                }
                            }
                        }
                        
                        // Color wheel button
                        Button(action: {
                            showColorPicker = true
                        }) {
                            HStack {
                                Spacer()
                                Text("SELECT UP TO 3 COLORS")
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(.white)
                                Spacer()
                            }
                            .frame(height: 200)
                            .background(
                                ZStack {
                                    RoundedRectangle(cornerRadius: 20)
                                        .fill(.ultraThinMaterial)
                                    
                                    RoundedRectangle(cornerRadius: 20)
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
                                RoundedRectangle(cornerRadius: 20)
                                    .stroke(Color.white.opacity(0.2), lineWidth: 1)
                            )
                            .overlay(
                                // Color wheel preview
                                ColorWheelPreview(selectedColors: session.outfitColors)
                            )
                        }
                    }
                    .padding(.horizontal, 20)
                    
                    // Continue button
                    Button(action: {
                        generateLook()
                    }) {
                        HStack {
                            if session.state == .generating {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            } else {
                                Text("Continue")
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
                    .disabled(session.occasion == nil || session.state == .generating)
                    .opacity(session.occasion == nil ? 0.5 : 1.0)
                }
            }
        }
        .sheet(isPresented: $showColorPicker) {
            ColorPickerView(selectedColors: $session.outfitColors)
        }
        .sheet(isPresented: $showCustomOccasionInput) {
            CustomOccasionView(text: $customOccasionText) {
                session.occasion = .custom
                session.customOccasion = customOccasionText
                showCustomOccasionInput = false
            }
        }
    }
    
    private func generateLook() {
        guard let faceImage = session.faceImage,
              let occasion = session.occasion else { return }
        
        session.state = .generating
        
        Task {
            do {
                let result = try await GeminiService.shared.generateMakeupLook(
                    faceImage: faceImage,
                    occasion: occasion,
                    customOccasion: session.customOccasion,
                    glamLevel: session.glamLevel,
                    goals: session.goals,
                    outfitColors: session.outfitColors
                )
                
                await MainActor.run {
                    session.generatedLookImage = result.image
                    session.generatedLookDescription = result.description
                    session.state = .reveal
                }
            } catch {
                await MainActor.run {
                    session.state = .intake
                    // Handle error
                }
            }
        }
    }
}

struct OccasionButton: View {
    let occasion: Occasion
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Image(systemName: occasion.icon)
                    .font(.system(size: 24))
                    .foregroundColor(.white)
                
                Text(occasion.rawValue)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.white)
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
                                colors: isSelected ?
                                    [Color.white.opacity(0.25), Color.white.opacity(0.15)] :
                                    [Color.white.opacity(0.15), Color.white.opacity(0.05)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                }
            )
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(
                        isSelected ? Color.white.opacity(0.6) : Color.white.opacity(0.2),
                        lineWidth: isSelected ? 2 : 1
                    )
            )
        }
    }
}

struct GoalButton: View {
    let goal: GlamGoal
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Image(systemName: goal.icon)
                    .font(.system(size: 24))
                    .foregroundColor(.white)
                
                Text(goal.rawValue)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.white)
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
                                colors: isSelected ?
                                    [Color.white.opacity(0.25), Color.white.opacity(0.15)] :
                                    [Color.white.opacity(0.15), Color.white.opacity(0.05)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                }
            )
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(
                        isSelected ? Color.white.opacity(0.6) : Color.white.opacity(0.2),
                        lineWidth: isSelected ? 2 : 1
                    )
            )
        }
    }
}

struct ColorWheelPreview: View {
    let selectedColors: [OutfitColor]
    
    var body: some View {
        ZStack {
            // Simplified color wheel representation
            ForEach(0..<12) { index in
                let hue = Double(index) / 12.0
                let color = Color(hue: hue, saturation: 1.0, brightness: 1.0)
                
                Circle()
                    .fill(color)
                    .frame(width: 30, height: 30)
                    .offset(
                        x: cos(Double(index) * 2 * .pi / 12) * 60,
                        y: sin(Double(index) * 2 * .pi / 12) * 60
                    )
            }
        }
    }
}

#Preview {
    IntakeBriefView(session: Session())
}

