<?php

namespace Application\Sonata\UserBundle\Controller;

use Application\Sonata\UserBundle\Form\Type\TopicType;
use Doctrine\ORM\OptimisticLockException;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;
use ThoughtBundle\Entity\Topic;

class TopicController extends Controller
{
    /**
     * @Route("/topic/create", name="sonata_user_topic_create")
     *
     * @param Request $request
     *
     * @return Response
     *
     * @throws OptimisticLockException
     */
    public function createAction(Request $request)
    {
        $em    = $this->get('doctrine.orm.entity_manager');
        $topic = new Topic();
        $topic->setUser($this->getUser());

        $form = $this->createForm(new TopicType(), $topic);
        $form->handleRequest($request);

        if (($form->isSubmitted()) && ($form->isValid())) {
            $topic = $form->getData();
            $em->persist($topic);
            $em->flush();
            return $this->redirectToRoute('sonata_user_topics');
        }

        return $this->render('ApplicationSonataUserBundle:Topic:create.html.twig', [
            'form' => $form->createView(),
        ]);
    }

    /**
     * @Route("/topic/{topicId}/edit", name="sonata_user_topic_edit", requirements={"topicId"="\d+"})
     *
     * @param Request $request
     * @param $topicId
     *
     * @return RedirectResponse|Response
     *
     * @throws OptimisticLockException
     */
    public function editAction(Request $request, $topicId)
    {
        $em = $this->get('doctrine.orm.entity_manager');
        /** @var Topic $topic */
        $topic = $em->getRepository(Topic::class)->find($topicId);
        $user  = $this->getUser();

        if ($topic->getUser() == $user) {
            $form = $this->createForm(new TopicType(), $topic);
            $form->handleRequest($request);

            if (($form->isSubmitted()) && ($form->isValid())) {
                $topic = $form->getData();
                $em->persist($topic);
                $em->flush();
                return $this->redirectToRoute('sonata_user_topics');
            }

            return $this->render('ApplicationSonataUserBundle:Topic:create.html.twig', [
                'form' => $form->createView(),
            ]);
        }

        $this->addFlash('danger', $this->get('translator')->trans('thought.topic.access_denied'));

        return $this->redirectToRoute('all_topics');
    }

    /**
     * @Route("/topic/{topicId}/delete", name="sonata_user_topic_remove", requirements={"topicId"="\d+"})
     */
    public function removeAction($topicId)
    {
        $em = $this->get('doctrine.orm.entity_manager');
        /** @var Topic $topic */
        $topic = $em->getRepository(Topic::class)->find($topicId);
        $em->remove($topic);
        $em->flush();

        return $this->redirectToRoute('sonata_user_topics');
    }

    /**
     * @Route("/topics", name="sonata_user_topics")
     *
     * @param Request $request
     *
     * @return Response
     */
    public function listAction(Request $request)
    {
        $em = $this->get('doctrine.orm.entity_manager');

        $topics = $em->getRepository(Topic::class)->findBy([
            'user' => $this->getUser(),
        ]);

//        dump($topics); die;

//        $paginator  = $this->get('knp_paginator');
//        $pagination = $paginator->paginate(
//            $topics,
//            $request->query->getInt('page', 1),
//            100
//        );
        return $this->render('ApplicationSonataUserBundle:Topic:list.html.twig', [
            'topics' => $topics,
        ]);
    }
}
