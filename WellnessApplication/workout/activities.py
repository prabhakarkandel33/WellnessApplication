"""
Specific Activities for Each Wellness Segment

These replace vague exercise descriptions with concrete, actionable activities.
Each activity includes duration, intensity, specific instructions, and metrics
for RL agent learning.
"""

ACTIVITIES_BY_SEGMENT = {
    "High Anxiety, Low Activity": {
        "physical": [
            {
                "name": "5-Min Gentle Stretching",
                "type": "exercise",
                "duration": 5,
                "intensity": "Low",
                "description": "Gentle stretching to release physical tension",
                "instructions": [
                    "1. Stand in comfortable position or sit in chair",
                    "2. Neck rolls: Rotate head slowly, 5 times each direction",
                    "3. Shoulder shrugs: Lift shoulders up, hold 2 seconds, release. Do 10 times",
                    "4. Wrist circles: Extend arms out, rotate wrists 10 times each direction",
                    "5. Hamstring stretch: Touch your toes gently, hold 20 seconds each leg",
                    "6. Gentle torso twist: Twist waist left/right, 10 times each side"
                ]
            },
            {
                "name": "Child's Pose Breathing (3 min)",
                "type": "exercise",
                "duration": 3,
                "intensity": "Low",
                "description": "Relaxing yoga pose with focused breathing to calm nervous system",
                "instructions": [
                    "1. Get on yoga mat or carpet, on hands and knees",
                    "2. Sit hips back to heels (or as far as comfortable)",
                    "3. Extend arms forward on the mat",
                    "4. Rest forehead on mat (or on your fists if that's more comfortable)",
                    "5. Take 10 slow, deep breaths",
                    "6. Focus on breathing in for 4 counts, out for 6 counts",
                    "7. Let your shoulders relax completely"
                ]
            },
            {
                "name": "Walking: 10 Minutes (Slow Pace)",
                "type": "exercise",
                "duration": 10,
                "intensity": "Low",
                "description": "Slow-paced walking in comfortable, safe environment",
                "instructions": [
                    "1. Choose a safe route: park, neighborhood, or indoors",
                    "2. Start walking at comfortable pace where you can talk easily",
                    "3. Focus on breathing: 4-count inhale, 6-count exhale",
                    "4. Let your arms swing naturally",
                    "5. Walk for 10 minutes without stopping",
                    "6. Notice surroundings: trees, sounds, sky (grounding technique)",
                    "7. No need to be fast - slow is perfect"
                ]
            }
        ],
        "mental": [
            {
                "name": "4-7-8 Breathing Technique (5 min)",
                "type": "meditation",
                "duration": 5,
                "intensity": "Low",
                "description": "Box breathing technique proven to reduce anxiety",
                "instructions": [
                    "1. Sit or lie down in comfortable position",
                    "2. Exhale completely through your mouth",
                    "3. Close your mouth, inhale slowly through nose for count of 4",
                    "4. Hold your breath for count of 7",
                    "5. Exhale slowly through mouth for count of 8",
                    "6. Repeat this cycle 4 times total",
                    "7. If you feel lightheaded, stop and breathe normally"
                ]
            },
            {
                "name": "Body Scan Meditation (10 min)",
                "type": "meditation",
                "duration": 10,
                "intensity": "Low",
                "description": "Systematic tension release through progressive awareness",
                "instructions": [
                    "1. Lie on back on carpet or yoga mat (or sit in comfortable chair)",
                    "2. Close your eyes",
                    "3. Take 3 deep breaths: in for 4, out for 6",
                    "4. Now focus on your toes. Notice any sensations. Consciously relax them",
                    "5. Move attention up: feet → ankles → calves → knees → thighs",
                    "6. Continue: hips → abdomen → chest → back → shoulders → arms → hands",
                    "7. Then: neck → jaw → face → head",
                    "8. Take 3 final deep breaths",
                    "9. Slowly open your eyes"
                ]
            },
            {
                "name": "Guided Progressive Relaxation (12 min)",
                "type": "meditation",
                "duration": 12,
                "intensity": "Low",
                "description": "Tense and release muscle groups to release anxiety",
                "instructions": [
                    "1. Lie comfortable on back",
                    "2. Tense your left foot for 5 seconds, then release completely",
                    "3. Tense your left calf for 5 seconds, then release",
                    "4. Tense your left thigh for 5 seconds, then release",
                    "5. Repeat steps 2-4 for right leg",
                    "6. Tense your abdomen for 5 seconds, then release",
                    "7. Tense your chest for 5 seconds, then release",
                    "8. Tense your left arm for 5 seconds, then release",
                    "9. Tense your right arm for 5 seconds, then release",
                    "10. Tense your shoulders and neck for 5 seconds, then release",
                    "11. Tense your face (squeeze all facial muscles) for 5 seconds, release",
                    "12. Rest for 2 minutes with all muscles relaxed"
                ]
            }
        ]
    },
    
    "Moderate Anxiety, Moderate Activity": {
        "physical": [
            {
                "name": "Brisk Walking: 20 Minutes",
                "type": "exercise",
                "duration": 20,
                "intensity": "Moderate",
                "description": "Faster-paced walking that elevates heart rate",
                "instructions": [
                    "1. Warm up with 2 minutes of slow walking",
                    "2. Increase pace to 'brisk' (where talking is possible but requires effort)",
                    "3. Maintain good posture: shoulders back, core engaged",
                    "4. Swing arms naturally at your sides",
                    "5. Maintain brisk pace for 15 minutes",
                    "6. Cool down with 3 minutes of slow walking",
                    "7. Optional: walk in park or outdoor setting for mental health benefits"
                ]
            },
            {
                "name": "Bodyweight Circuit: 15 Minutes",
                "type": "exercise",
                "duration": 15,
                "intensity": "Moderate",
                "description": "Compound movements using body weight for strength and cardio",
                "instructions": [
                    "SET 1 (Repeat 3 times):",
                    "1. Push-ups: 8-10 repetitions (on knees or incline if needed)",
                    "2. Bodyweight squats: 15 repetitions",
                    "3. Plank: Hold for 30 seconds",
                    "4. Rest for 60 seconds between sets",
                    "Tips:",
                    "- For push-ups: hands shoulder-width, lower until elbows bend to 90 degrees",
                    "- For squats: feet shoulder-width, lower hips like sitting in chair",
                    "- For planks: straight line from head to heels, don't let hips sag"
                ]
            },
        ],
        "mental": [
            {
                "name": "Gratitude Journaling: 10 Minutes",
                "type": "journaling",
                "duration": 10,
                "intensity": "Low",
                "description": "Structured journaling focusing on gratitude and positive experiences",
                "instructions": [
                    "1. Find quiet space with pen/paper or device",
                    "2. Write at top of page: 'Today I'm grateful for...' and today's date",
                    "3. List 5-7 specific things you're grateful for (no minimum length)",
                    "4. For each item, write 1-2 sentences WHY you're grateful for it",
                    "Examples of what to write:",
                    "- 'My morning coffee - it gave me energy and a calm moment'",
                    "- 'My friend called - I felt remembered and cared for'",
                    "- 'The sunshine - it lifted my mood immediately'",
                    "5. Read back what you wrote and reflect on how it makes you feel"
                ]
            },
            {
                "name": "Mindfulness Meditation: 10 Minutes",
                "type": "meditation",
                "duration": 10,
                "intensity": "Moderate",
                "description": "Focused attention meditation to improve concentration and reduce anxiety",
                "instructions": [
                    "1. Sit comfortably with spine straight, feet on floor or crossed",
                    "2. Close your eyes or look down softly",
                    "3. Focus your attention on your natural breath",
                    "4. Count each exhale: 1, 2, 3... up to 10",
                    "5. When you reach 10, start counting back: 10, 9, 8... down to 1",
                    "6. If your mind wanders (it will!), gently bring it back to counting",
                    "7. No judgment - wandering is normal, just notice and return",
                    "8. Continue for 10 minutes",
                    "Don't worry if you lose count - just start over"
                ]
            }
        ]
    },
    
    "Low Anxiety, High Activity": {
        "physical": [
            {
                "name": "HIIT Workout: 20 Minutes",
                "type": "exercise",
                "duration": 20,
                "intensity": "High",
                "description": "High Intensity Interval Training for cardio and strength",
                "instructions": [
                    "WARM-UP (2 min): Light jogging or jumping jacks",
                    "MAIN WORKOUT (16 min) - Repeat 4 times:",
                    "  1. 30 seconds: Burpees (squat, hands to ground, jump back, jump forward)",
                    "  2. 30 seconds: High knees running in place",
                    "  3. 30 seconds: Push-up to down-dog (push-up, lift hips high)",
                    "  4. 30 seconds: Mountain climbers",
                    "  5. 60 seconds: REST (walking, deep breathing)",
                    "COOL-DOWN (2 min): Stretching and slow breathing",
                    "Total: 20 minutes of intense full-body workout"
                ]
            },
            {
                "name": "Running: 30 Minutes (Steady State)",
                "type": "exercise",
                "duration": 30,
                "intensity": "High",
                "description": "Steady-pace running for cardiovascular fitness",
                "instructions": [
                    "1. Warm-up with 2 minutes of walking",
                    "2. Start running at comfortable pace (can speak in short sentences)",
                    "3. Maintain pace for 25 minutes",
                    "4. Cool-down: 3 minutes of walking and stretching",
                    "Tips:",
                    "- Wear proper running shoes",
                    "- Land on midfoot, not heels",
                    "- Keep shoulders relaxed",
                    "- Choose a safe route (street, track, or treadmill)"
                ]
            },
            {
                "name": "Strength Training: 30 Minutes",
                "type": "exercise",
                "duration": 30,
                "intensity": "High",
                "description": "Resistance-based workout targeting major muscle groups",
                "instructions": [
                    "Equipment: Dumbbells or resistance bands (or use bodyweight)",
                    "WARM-UP (3 min): Light cardio",
                    "WORKOUT (25 min):",
                    "  - Dumbbell squats: 12 reps × 3 sets",
                    "  - Dumbbell bench press: 12 reps × 3 sets",
                    "  - Dumbbell rows: 12 reps × 3 sets",
                    "  - Dumbbell shoulder press: 10 reps × 3 sets",
                    "  - Rest 60-90 seconds between sets",
                    "COOL-DOWN (2 min): Stretching",
                    "Use weight that challenges last 2-3 reps"
                ]
            }
        ],
        "mental": [
            {
                "name": "Performance Visualization: 10 Minutes",
                "type": "meditation",
                "duration": 10,
                "intensity": "Moderate",
                "description": "Mental rehearsal of upcoming goals or challenges",
                "instructions": [
                    "1. Sit comfortably, close eyes",
                    "2. Think of upcoming goal or challenge (workout, presentation, etc.)",
                    "3. Visualize yourself succeeding in vivid detail:",
                    "   - What do you see? (colors, details)",
                    "   - What do you feel? (confident, strong)",
                    "   - What do you hear? (applause, encouragement)",
                    "4. See yourself performing perfectly",
                    "5. Feel the emotions of success",
                    "6. Open eyes and carry this confidence forward",
                    "Duration: 10 minutes of detailed visualization"
                ]
            },
            {
                "name": "Goal-Setting & Planning: 15 Minutes",
                "type": "journaling",
                "duration": 15,
                "intensity": "Moderate",
                "description": "Strategic planning for fitness and personal growth goals",
                "instructions": [
                    "1. Find quiet space with pen/paper",
                    "2. Write: 'My Fitness Goals for the Next Month'",
                    "3. List 2-3 specific goals (e.g., 'Run 5K without stopping')",
                    "4. For each goal, write:",
                    "   GOAL: Be specific and measurable",
                    "   WHY: Why does this matter to me?",
                    "   HOW: What steps will I take?",
                    "   OBSTACLES: What might get in the way?",
                    "   SOLUTIONS: How will I overcome obstacles?",
                    "5. Create weekly action steps",
                    "Example Goal: Run 5K without stopping by end of month",
                    "  STEPS: Monday/Wednesday/Friday runs, gradually increase distance"
                ]
            }
        ]
    },
    
    "Physical Health Risk": {
        "physical": [
            {
                "name": "Gentle Walking: 15 Minutes",
                "type": "exercise",
                "duration": 15,
                "intensity": "Low",
                "description": "Low-impact walking to improve cardiovascular health",
                "instructions": [
                    "1. Wear comfortable, supportive shoes",
                    "2. Walk on flat, safe surface (sidewalk, track, or treadmill)",
                    "3. Maintain comfortable pace (can talk easily)",
                    "4. Walk continuously for 15 minutes",
                    "5. Focus on good posture: shoulders back, eyes forward",
                    "6. If tired, slower pace is fine - consistency is key",
                    "Safety:",
                    "- Stop if you feel chest pain, dizziness, or severe shortness of breath",
                    "- Stay hydrated",
                    "- Walk during daylight or in well-lit areas"
                ]
            },
            {
                "name": "Swimming: 20 Minutes",
                "type": "exercise",
                "duration": 20,
                "intensity": "Moderate",
                "description": "Low-impact, full-body cardio exercise",
                "instructions": [
                    "1. Use community pool or fitness center",
                    "2. Start with 2 minutes of pool walking (water up to waist)",
                    "3. Swim or water-walk for 15 minutes at comfortable pace",
                    "   - If swimming: use whatever stroke is comfortable (freestyle, breaststroke)",
                    "   - If water-walking: walk in chest-deep water",
                    "4. Cool down with 3 minutes of easy movement",
                    "Benefits:",
                    "- Water supports your weight (easier on joints)",
                    "- Great for people with arthritis or joint pain"
                ]
            },
            {
                "name": "Flexibility & Balance: 15 Minutes",
                "type": "exercise",
                "duration": 15,
                "intensity": "Low",
                "description": "Improve mobility and reduce fall risk",
                "instructions": [
                    "1. Stand with feet shoulder-width apart, hold wall/chair for balance",
                    "2. Hamstring stretch: Hold left knee, gently pull leg up. Hold 20 seconds. Repeat other leg",
                    "3. Calf stretch: Place hands on wall, step back with one leg, lean in. Hold 20 seconds each",
                    "4. Hip circles: Hands on hips, make slow circles with hips. 10 each direction",
                    "5. Standing on one leg: Hold wall, stand on one leg for 20 seconds. Repeat other leg",
                    "6. Gentle torso twist: Keep hips still, twist shoulders left/right. 10 times each",
                    "7. Arm circles: Extend arms out, make slow circles. 10 forward, 10 backward",
                    "Take your time - this is about mobility, not speed"
                ]
            }
        ],
        "mental": [
            {
                "name": "Motivation Boost: Positive Affirmations (5 min)",
                "type": "meditation",
                "duration": 5,
                "intensity": "Low",
                "description": "Use positive self-talk to build confidence and motivation",
                "instructions": [
                    "1. Sit comfortably",
                    "2. Close your eyes",
                    "3. Repeat these affirmations out loud or silently (3 times each):",
                    "   'I am capable of taking care of my health'",
                    "   'Every step I take is progress'",
                    "   'My body is getting stronger every day'",
                    "   'I deserve to feel good'",
                    "4. Feel the truth in these words",
                    "5. Open eyes and carry this confidence forward"
                ]
            },
            {
                "name": "Habit Tracking & Celebration: 10 Minutes",
                "type": "journaling",
                "duration": 10,
                "intensity": "Low",
                "description": "Track habits and celebrate small wins to build momentum",
                "instructions": [
                    "1. Write today's date",
                    "2. List activities completed today:",
                    "   ☐ Completed workout",
                    "   ☐ Completed meditation",
                    "   ☐ Took medications on time",
                    "   ☐ Got enough sleep",
                    "   ☐ Drank enough water",
                    "3. Put a checkmark next to each completed item",
                    "4. Write: 'Today I'm proud of myself because...' and list achievements",
                    "5. Even small wins count! Did you try? That's a win.",
                    "6. Rate your day: 1-5 stars",
                    "Goal: Build consistency over perfection"
                ]
            }
        ]
    }
}
