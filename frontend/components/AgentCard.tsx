import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Avatar, AvatarFallback } from "./ui/avatar";
import { UIAgent } from "@/lib/types";
import { motion } from "framer-motion";

interface AgentCardProps {
  agent: UIAgent;
  index: number;
}

export function AgentCard({ agent, index }: AgentCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.15, duration: 0.4 }}
    >
      <Card className="overflow-hidden bg-[#1b1f27] border-[#3b4354] pt-0">
        <CardHeader className={`${agent.color} text-white pb-3 pt-4`}>
          <div className="flex items-center gap-3">
            <Avatar className="h-10 w-10 border-2 border-white/20">
              <AvatarFallback className="bg-white/10 text-white text-sm">
                {agent.avatar}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <CardTitle className="flex items-center gap-2 text-base">
                {agent.name}
                <span className="material-symbols-outlined text-base">smart_toy</span>
              </CardTitle>
              <p className="text-sm opacity-90 truncate">{agent.role}</p>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-2.5">
          <div>
            <h4 className="text-sm mb-1.5 flex items-center gap-1.5 text-white">
              <span className="material-symbols-outlined text-sm">auto_awesome</span>
              Personality
            </h4>
            <p className="text-sm text-[#9ca6ba] leading-relaxed">{agent.personality}</p>
          </div>
          <div>
            <h4 className="text-sm mb-2 text-white">Key Strengths</h4>
            <div className="flex flex-wrap gap-1.5">
              {agent.strengths.map((strength: string, idx: number) => (
                <Badge key={idx} variant="secondary" className="bg-[#282e39] text-[#9ca6ba] border-[#3b4354] text-xs">
                  {strength}
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
