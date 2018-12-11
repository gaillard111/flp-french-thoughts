<?php

namespace ThoughtBundle\Controller;

use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Annotation\Route;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use ThoughtBundle\Entity\Topic;

class TopicController extends Controller
{
    /**
     * @Route("/topics/{topicId}", name="topic_page", requirements={"topicId"="\d+"})
     */
    public function indexAction(Request $request)
    {
        $topicId = $request->get('topicId');
        $em = $this->getDoctrine()->getManager();
        $topic = $em->getRepository(Topic::class)->find($topicId);

        return $this->render('@Thought/Topic/topicPage.html.twig', [
            'topic'    =>  $topic,
        ]);
    }

    /**
     * @Route("/topics", name="all_topics")
     * @param Request $request
     * @return \Symfony\Component\HttpFoundation\Response
     */
    public function AllAction(Request $request)
    {
        $em = $this->get('doctrine.orm.entity_manager');

        $topics = $em->getRepository(Topic::class)->findAll();

//        dump($topics); die;

//        $paginator  = $this->get('knp_paginator');
//        $pagination = $paginator->paginate(
//            $topics,
//            $request->query->getInt('page', 1),
//            100
//        );
        return $this->render('ThoughtBundle:Topic:list.html.twig', [
            'topics' => $topics,
        ]);
    }
}
